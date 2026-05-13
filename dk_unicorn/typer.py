import inspect
import typing
from datetime import date, datetime, time, timedelta
from typing import Any, Union, get_type_hints as _get_type_hints
from uuid import UUID

from django.db.models import Model, QuerySet
from django.utils.dateparse import parse_date, parse_datetime, parse_duration, parse_time

from dk_unicorn.typing import QuerySetType

try:
    from cachetools import LRUCache
except ImportError:
    from functools import lru_cache


def _parse_bool(value):
    return str(value) == "True"


CASTERS = {
    datetime: parse_datetime,
    time: parse_time,
    date: parse_date,
    timedelta: parse_duration,
    UUID: UUID,
    bool: _parse_bool,
}

type_hints_cache = LRUCache(maxsize=100)
function_signature_cache = LRUCache(maxsize=100)


def _check_pydantic(cls):
    try:
        from pydantic import BaseModel as PydanticBaseModel
        return isinstance(cls, type) and issubclass(cls, PydanticBaseModel)
    except ImportError:
        return False


def get_type_hints(obj):
    cache_key = id(obj)
    if cache_key in type_hints_cache:
        return type_hints_cache[cache_key]

    target = obj
    if not isinstance(obj, type) and not inspect.ismodule(obj) and not inspect.isroutine(obj):
        target = obj.__class__

    try:
        hints = _get_type_hints(target)
    except Exception:
        hints = getattr(target, "__annotations__", {})

    type_hints_cache[cache_key] = hints
    return hints


def _get_type_args(type_hint):
    return getattr(type_hint, "__args__", None)


def _get_origin(type_hint):
    return getattr(type_hint, "__origin__", None)


def cast_value(type_hint, value):
    origin = _get_origin(type_hint)
    args = _get_type_args(type_hint)

    if origin is Union or (hasattr(typing, "UnionType") and isinstance(type_hint, typing.UnionType)):
        if args:
            if type(None) in args and value is None:
                return None
            for arg in args:
                if arg is type(None):
                    continue
                try:
                    return cast_value(arg, value)
                except (ValueError, TypeError):
                    continue
        return value

    if origin is list:
        if isinstance(value, list) and args:
            return [cast_value(args[0], v) for v in value]
        return value

    if origin is tuple:
        if isinstance(value, (list, tuple)) and args:
            if len(args) == 1:
                return tuple(cast_value(args[0], v) for v in value)
            else:
                return tuple(cast_value(t, v) for t, v in zip(args, value))
        return value

    if origin is dict:
        if isinstance(value, dict) and args and len(args) == 2:
            return {k: cast_value(args[1], v) for k, v in value.items()}
        return value

    if type_hint in CASTERS:
        caster = CASTERS[type_hint]
        if type_hint is bool:
            return caster(value)

        if type_hint in (datetime, date) and isinstance(value, (int, float)):
            from datetime import timezone
            dt = datetime.fromtimestamp(value, tz=timezone.utc)
            if type_hint is date:
                return dt.date()
            return dt

        try:
            result = caster(value)
            if result is not None:
                return result
        except (ValueError, TypeError):
            pass
        return value

    if isinstance(type_hint, type):
        import dataclasses
        if dataclasses.is_dataclass(type_hint) and isinstance(value, dict):
            return type_hint(**value)

        if _check_pydantic(type_hint) and isinstance(value, dict):
            return type_hint(**value)

        if issubclass(type_hint, Model) and isinstance(value, dict):
            return _construct_model(type_hint, value)

        try:
            return type_hint(value)
        except (ValueError, TypeError):
            pass

    return value


def cast_attribute_value(obj, name, value):
    hints = get_type_hints(obj)
    type_hint = hints.get(name)

    if type_hint is None:
        return value

    if isinstance(value, QuerySet):
        return value

    import dataclasses
    if dataclasses.is_dataclass(type(value)):
        return value

    return cast_value(type_hint, value)


def get_method_arguments(func):
    cache_key = id(func)
    if cache_key in function_signature_cache:
        return function_signature_cache[cache_key]

    sig = inspect.signature(func)
    result = list(sig.parameters.keys())
    function_signature_cache[cache_key] = result
    return result


def is_queryset(obj, type_hint, value):
    if isinstance(value, QuerySet):
        return True

    origin = _get_origin(type_hint)
    if origin is Union or (hasattr(typing, "UnionType") and isinstance(type_hint, typing.UnionType)):
        args = _get_type_args(type_hint) or ()
        for arg in args:
            if _is_queryset_type(arg):
                return True

    return _is_queryset_type(type_hint)


def _is_queryset_type(type_hint):
    origin = _get_origin(type_hint)
    if origin is not None:
        try:
            if issubclass(origin, QuerySet):
                return True
        except TypeError:
            pass
    if isinstance(type_hint, type):
        try:
            if issubclass(type_hint, (QuerySet, QuerySetType)):
                return True
        except TypeError:
            pass
    return False


def create_queryset(obj, type_hint, value):
    origin = _get_origin(type_hint)
    args = _get_type_args(type_hint)

    model_type = None

    if origin is Union or (hasattr(typing, "UnionType") and isinstance(type_hint, typing.UnionType)):
        for arg in (args or ()):
            if _is_queryset_type(arg):
                inner_args = _get_type_args(arg)
                if inner_args:
                    model_type = inner_args[0]
                break
    elif args:
        model_type = args[0]

    if model_type is None or not isinstance(model_type, type) or not issubclass(model_type, Model):
        return value

    qs = model_type.objects.none()

    if isinstance(value, list):
        models = []
        for item in value:
            if isinstance(item, dict):
                models.append(_construct_model(model_type, item))
            elif isinstance(item, model_type):
                models.append(item)
        qs._result_cache = models

    return qs


def _construct_model(model_type, model_data):
    instance = model_type()
    for field in model_type._meta.fields:
        if field.name in model_data:
            setattr(instance, field.name, model_data[field.name])
        elif field.attname in model_data:
            setattr(instance, field.attname, model_data[field.attname])
        elif field.name == "pk" and "pk" in model_data:
            setattr(instance, field.attname, model_data["pk"])
    if "pk" in model_data:
        instance.pk = model_data["pk"]
    return instance
