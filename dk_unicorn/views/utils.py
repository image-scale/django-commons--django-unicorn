import logging
from dataclasses import is_dataclass
from typing import Any, Union, get_args, get_origin

from django.db.models import Model

from dk_unicorn.components import UnicornField, UnicornView
from dk_unicorn.decorators import timed
from dk_unicorn.typer import cast_value, create_queryset, get_type_hints, is_queryset

try:
    from types import UnionType
except ImportError:
    UnionType = Union

logger = logging.getLogger(__name__)


@timed
def set_property_from_data(
    component_or_field: UnicornView | UnicornField | Model,
    name: str,
    value: Any,
    *,
    ignore_m2m: bool = False,
) -> None:
    try:
        if not hasattr(component_or_field, name):
            return

        if isinstance(component_or_field, UnicornView) and not component_or_field._is_public(name):
            return
    except ValueError:
        return

    field = getattr(component_or_field, name)
    component_field_is_model_or_unicorn_field = _is_component_field_model_or_unicorn_field(component_or_field, name)

    if isinstance(component_or_field, Model) and not isinstance(value, dict):
        try:
            model_field = component_or_field._meta.get_field(name)

            if model_field.is_relation and model_field.many_to_one:
                if isinstance(value, Model):
                    setattr(component_or_field, name, value)
                elif hasattr(model_field, "attname"):
                    setattr(component_or_field, str(model_field.attname), value)

                return
        except Exception:
            pass

    if component_field_is_model_or_unicorn_field:
        field = getattr(component_or_field, name)

        if isinstance(value, dict):
            for key in value.keys():
                key_value = value[key]
                set_property_from_data(field, key, key_value, ignore_m2m=ignore_m2m)
    elif hasattr(field, "related_val"):
        if not ignore_m2m:
            field.set(value)
    else:
        type_hints = get_type_hints(component_or_field)
        type_hint = type_hints.get(name)

        if is_queryset(field, type_hint, value):
            value = create_queryset(field, type_hint, value)
        elif type_hint:
            if is_dataclass(type_hint):
                value = type_hint(**value)
            else:
                try:
                    value = cast_value(type_hint, value)
                except TypeError:
                    pass

        if hasattr(component_or_field, "_set_property"):
            component_or_field._set_property(
                name, value, call_updating_method=True, call_updated_method=False
            )
        else:
            setattr(component_or_field, name, value)


@timed
def _is_component_field_model_or_unicorn_field(
    component_or_field: UnicornView | UnicornField | Model,
    name: str,
) -> bool:
    field = getattr(component_or_field, name)

    if isinstance(field, (Model, UnicornField)):
        return True

    is_subclass_of_model = False
    is_subclass_of_unicorn_field = False

    try:
        component_type_hints = get_type_hints(component_or_field)

        if name in component_type_hints:
            type_hint = component_type_hints[name]

            if get_origin(type_hint) is Union or get_origin(type_hint) is UnionType:
                for arg in get_args(type_hint):
                    if arg is not type(None):
                        type_hint = arg
                        break

            is_subclass_of_model = issubclass(type_hint, Model)

            if not is_subclass_of_model:
                is_subclass_of_unicorn_field = issubclass(type_hint, UnicornField)

            if field is None:
                if is_subclass_of_model or is_subclass_of_unicorn_field:
                    field = type_hint()
                    setattr(component_or_field, name, field)
    except TypeError:
        pass

    return is_subclass_of_model or is_subclass_of_unicorn_field
