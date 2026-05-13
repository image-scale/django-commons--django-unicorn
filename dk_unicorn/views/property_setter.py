from dk_unicorn.errors import UnicornViewError
from dk_unicorn.signals import (
    component_property_resolved,
    component_property_updated,
    component_property_updating,
)


def set_property_value(component, property_name, property_value, data=None, call_resolved_method=True):
    if property_name is None:
        raise AssertionError("Property name is required")
    if property_value is None:
        raise AssertionError("Property value is required")

    property_name_root = property_name.split(".")[0]
    if not component._is_public(property_name_root):
        raise UnicornViewError(f"'{property_name_root}' is not a valid property name")

    if data is None:
        data = {}

    component.updating(property_name, property_value)
    component_property_updating.send(
        sender=component.__class__, component=component, name=property_name, value=property_value
    )

    property_name_parts = property_name.split(".")
    for part in property_name_parts:
        if part.startswith("__") and part.endswith("__"):
            raise AssertionError("Invalid property name")

    component_or_field = component
    data_or_dict = data

    for idx, part in enumerate(property_name_parts):
        if hasattr(component_or_field, part):
            if idx == len(property_name_parts) - 1:
                if hasattr(component_or_field, "_set_property"):
                    component_or_field._set_property(
                        part,
                        property_value,
                        call_updating_method=False,
                        call_updated_method=True,
                        call_resolved_method=call_resolved_method,
                    )
                else:
                    property_name_snake = property_name.replace(".", "_")
                    updating_fn = f"updating_{property_name_snake}"
                    updated_fn = f"updated_{property_name_snake}"
                    resolved_fn = f"resolved_{property_name_snake}"

                    if hasattr(component, updating_fn):
                        getattr(component, updating_fn)(property_value)

                    setattr(component_or_field, part, property_value)

                    if hasattr(component, updated_fn):
                        getattr(component, updated_fn)(property_value)

                    if call_resolved_method and hasattr(component, resolved_fn):
                        getattr(component, resolved_fn)(property_value)

                data_or_dict[part] = property_value
            else:
                component_or_field = getattr(component_or_field, part)
                data_or_dict = data_or_dict.get(part, {})
        elif isinstance(component_or_field, dict):
            if idx == len(property_name_parts) - 1:
                component_or_field[part] = property_value
                data_or_dict[part] = property_value
            else:
                component_or_field = component_or_field[part]
                data_or_dict = data_or_dict.get(part, {})
        elif isinstance(component_or_field, (list,)):
            part_int = int(part)
            if idx == len(property_name_parts) - 1:
                component_or_field[part_int] = property_value
                data_or_dict[part_int] = property_value
            else:
                component_or_field = component_or_field[part_int]
                data_or_dict = data_or_dict[part_int]
        else:
            break

    component.updated(property_name, property_value)
    component_property_updated.send(
        sender=component.__class__, component=component, name=property_name, value=property_value
    )

    if call_resolved_method:
        component.resolved(property_name, property_value)
        component_property_resolved.send(
            sender=component.__class__, component=component, name=property_name, value=property_value
        )
