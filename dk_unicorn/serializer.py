import orjson
from decimal import Decimal
from types import MappingProxyType

from django.db.models import Model, QuerySet


class JSONDecodeError(Exception):
    pass


class InvalidFieldNameError(Exception):
    def __init__(self, field_name="", data=None):
        self.field_name = field_name
        self.data = data or {}
        super().__init__(f"Invalid field name: {field_name}")


class InvalidFieldAttributeError(Exception):
    def __init__(self, field_name="", field_attr="", data=None):
        self.field_name = field_name
        self.field_attr = field_attr
        self.data = data or {}
        super().__init__(f"Invalid field attribute: {field_name}.{field_attr}")


def _get_model_dict(model):
    from django.core.serializers import serialize
    import json

    serialized = serialize("json", [model])
    data = json.loads(serialized)
    result = data[0].get("fields", {})
    result["pk"] = model.pk

    for field in model._meta.get_fields():
        if field.many_to_many:
            try:
                if field.auto_created:
                    attr_name = field.related_name or f"{field.name}_set"
                else:
                    attr_name = field.name
                related_manager = getattr(model, attr_name)
                result[attr_name] = list(related_manager.values_list("pk", flat=True))
            except (ValueError, AttributeError):
                pass

    return result


def _json_serializer(obj):
    if isinstance(obj, Model):
        return _get_model_dict(obj)
    if isinstance(obj, QuerySet):
        return [_get_model_dict(m) for m in obj]
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, MappingProxyType):
        return dict(obj)
    if hasattr(obj, "to_json"):
        return obj.to_json()

    try:
        from pydantic import BaseModel as PydanticBaseModel
        if isinstance(obj, PydanticBaseModel):
            return obj.dict()
    except ImportError:
        pass

    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _fix_floats(data):
    if isinstance(data, dict):
        for key in list(data.keys()):
            val = data[key]
            if isinstance(val, float):
                data[key] = str(val)
            elif isinstance(val, dict):
                _fix_floats(val)
            elif isinstance(val, (list, tuple)):
                if isinstance(val, tuple):
                    data[key] = list(val)
                    val = data[key]
                _fix_floats_list(val)
    elif isinstance(data, list):
        _fix_floats_list(data)


def _fix_floats_list(lst):
    for i, val in enumerate(lst):
        if isinstance(val, float):
            lst[i] = str(val)
        elif isinstance(val, dict):
            _fix_floats(val)
        elif isinstance(val, (list, tuple)):
            if isinstance(val, tuple):
                lst[i] = list(val)
                val = lst[i]
            _fix_floats_list(val)


def _sort_dict(data):
    if isinstance(data, dict):
        def sort_key(k):
            try:
                return (0, int(k))
            except (ValueError, TypeError):
                return (1, k)
        return {k: _sort_dict(v) for k, v in sorted(data.items(), key=lambda item: sort_key(item[0]))}
    if isinstance(data, list):
        return [_sort_dict(v) for v in data]
    return data


def _exclude_field_attributes(dict_data, exclude_field_attributes):
    if not exclude_field_attributes:
        return dict_data

    for attr_path in exclude_field_attributes:
        parts = attr_path.split(".")
        current = dict_data
        field_name = parts[0]

        if field_name not in current:
            raise InvalidFieldNameError(field_name=field_name, data=dict_data)

        for part in parts[1:-1]:
            if not isinstance(current.get(field_name), dict):
                raise InvalidFieldAttributeError(field_name=field_name, field_attr=part, data=dict_data)
            current = current[field_name]
            field_name = part

        last = parts[-1]
        if isinstance(current.get(field_name) if len(parts) > 1 else current, dict):
            target = current[field_name] if len(parts) > 1 else current
            if last not in target:
                raise InvalidFieldAttributeError(
                    field_name=parts[-2] if len(parts) > 1 else field_name,
                    field_attr=last,
                    data=dict_data,
                )
            del target[last]

    return dict_data


def dumps(data, *, fix_floats=True, exclude_field_attributes=None, sort_dict=True):
    raw = orjson.dumps(data, default=_json_serializer)
    result = orjson.loads(raw)

    if fix_floats and isinstance(result, dict):
        _fix_floats(result)

    if exclude_field_attributes:
        _exclude_field_attributes(result, exclude_field_attributes)

    if sort_dict and isinstance(result, dict):
        result = _sort_dict(result)

    return orjson.dumps(result).decode("utf-8")


def loads(string):
    try:
        return orjson.loads(string)
    except orjson.JSONDecodeError as e:
        raise JSONDecodeError(str(e)) from e


def model_value(model, *fields):
    model_dict = _get_model_dict(model)
    if fields:
        return {k: v for k, v in model_dict.items() if k in fields}
    return model_dict
