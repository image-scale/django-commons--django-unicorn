import copy
import logging
from functools import wraps
from typing import Any, Union, get_origin

import orjson
from django.db.models import Model
from django.forms import ValidationError
from django.http import HttpRequest, JsonResponse
from django.http.response import HttpResponseNotModified
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_POST

from dk_unicorn.cacher import cache_full_tree
from dk_unicorn.components import UnicornView
from dk_unicorn.errors import RenderNotModifiedError, UnicornViewError
from dk_unicorn.signals import (
    component_completed,
    component_hydrated,
    component_method_called,
    component_method_calling,
    component_post_parsed,
    component_pre_parsed,
    component_rendered,
)
from dk_unicorn.call_method_parser import InvalidKwargError, parse_call_method_name, parse_kwarg
from dk_unicorn.typer import cast_value, get_type_hints
from dk_unicorn.utils import get_method_arguments
from dk_unicorn.views.action import CallMethod, Refresh, Reset, SyncInput, Toggle
from dk_unicorn.views.objects import Return
from dk_unicorn.views.property_setter import set_property_value
from dk_unicorn.views.request import ComponentRequest
from dk_unicorn.views.response import ComponentResponse
from dk_unicorn.views.utils import set_property_from_data

try:
    from types import UnionType
except ImportError:
    UnionType = Union

logger = logging.getLogger(__name__)


def _get_property_value(component, property_name):
    if property_name is None:
        raise AssertionError("property_name name is required")

    property_name_parts = property_name.split(".")
    component_or_field = component

    for idx, part in enumerate(property_name_parts):
        if hasattr(component_or_field, part):
            if idx == len(property_name_parts) - 1:
                return getattr(component_or_field, part)
            else:
                component_or_field = getattr(component_or_field, part)
        elif isinstance(component_or_field, dict):
            if idx == len(property_name_parts) - 1:
                return component_or_field[part]
            else:
                component_or_field = component_or_field[part]


def _call_method_name(component, method_name, args, kwargs):
    if method_name is not None and hasattr(component, method_name):
        if not component._is_public(method_name):
            raise UnicornViewError(f"'{method_name}' is not a valid method name")

        func = getattr(component, method_name)

        parsed_args = []
        parsed_kwargs = {}
        arguments = get_method_arguments(func)
        type_hints = get_type_hints(func)

        for argument in arguments:
            if argument in type_hints:
                type_hint = type_hints[argument]

                if (
                    not isinstance(type_hint, type)
                    and get_origin(type_hint) is not Union
                    and get_origin(type_hint) is not UnionType
                ):
                    continue

                is_model = False
                try:
                    is_model = isinstance(type_hint, type) and issubclass(type_hint, Model)
                except TypeError:
                    pass

                if is_model:
                    if not kwargs:
                        if len(args) > len(parsed_args):
                            value = args[len(parsed_args)]
                            parsed_args.append(type_hint.objects.get(pk=value))
                    else:
                        value = kwargs.get("pk")
                        parsed_kwargs[argument] = type_hint.objects.get(pk=value)
                elif argument in kwargs:
                    parsed_kwargs[argument] = cast_value(type_hint, kwargs[argument])
                elif len(args) > len(parsed_args):
                    parsed_args.append(cast_value(type_hint, args[len(parsed_args)]))
            elif argument in kwargs:
                parsed_kwargs[argument] = kwargs[argument]
            elif len(args) > len(parsed_args):
                parsed_args.append(args[len(parsed_args)])

        if parsed_args:
            return func(*parsed_args, **parsed_kwargs)
        elif parsed_kwargs:
            return func(**parsed_kwargs)
        else:
            return func()


def handle_error(view_func):
    def wrapped_view(*args, **kwargs):
        try:
            return view_func(*args, **kwargs)
        except UnicornViewError as e:
            return JsonResponse({"error": str(e)})
        except RenderNotModifiedError:
            return HttpResponseNotModified()
        except AssertionError as e:
            return JsonResponse({"error": str(e)})

    return wraps(view_func)(wrapped_view)


@handle_error
@ensure_csrf_cookie
@csrf_protect
@require_POST
def message(request: HttpRequest, component_name: str = None) -> JsonResponse:
    if not component_name:
        raise AssertionError("Missing component name in url")

    component_request = ComponentRequest(request, component_name)

    component = UnicornView.create(
        component_id=component_request.id,
        component_name=component_request.name,
        request=request,
    )

    if component.request is None:
        component.request = request

    original_data = copy.deepcopy(component_request.data)

    component.pre_parse()
    component_pre_parsed.send(sender=component.__class__, component=component)

    for property_name, property_value in component_request.data.items():
        set_property_from_data(component, property_name, property_value)

    component.post_parse()
    component_post_parsed.send(sender=component.__class__, component=component)

    component.hydrate()
    component_hydrated.send(sender=component.__class__, component=component)

    is_reset_called = False
    is_refresh_called = False
    validate_all_fields = False
    return_data = Return("", [], {})
    partials = []

    for action in component_request.action_queue:
        if action.partials:
            partials.extend(action.partials)

        if isinstance(action, SyncInput):
            call_resolved_method = True

            if len(component_request.action_queue) > 1:
                call_resolved_method = False
                last_action = component_request.action_queue[-1]
                if (
                    isinstance(last_action, SyncInput)
                    and last_action.name == action.name
                    and last_action.value == action.value
                ):
                    call_resolved_method = True

            set_property_value(
                component,
                action.name,
                action.value,
                component_request.data,
                call_resolved_method=call_resolved_method,
            )

        elif isinstance(action, Reset):
            component = UnicornView.create(
                component_id=component_request.id,
                component_name=component_request.name,
                request=request,
                use_cache=False,
            )
            component.errors = {}
            is_reset_called = True

        elif isinstance(action, Refresh):
            component = UnicornView.create(
                component_id=component_request.id,
                component_name=component_request.name,
                request=request,
            )
            for pname, pvalue in component_request.data.items():
                set_property_from_data(component, pname, pvalue)
            component.hydrate()
            is_refresh_called = True

        elif isinstance(action, Toggle):
            for property_name in action.args:
                property_value = _get_property_value(component, property_name)
                property_value = not property_value
                set_property_value(component, property_name, property_value)

        elif isinstance(action, CallMethod):
            call_method_name = action.method_name
            method_args = action.args
            method_kwargs = action.kwargs

            parent_component = None
            parents = call_method_name.split(".")
            for parent in parents:
                if parent == "$parent":
                    parent_component = component.parent
                    if parent_component:
                        parent_component.force_render = True
                    call_method_name = call_method_name[8:]

            (method_name, parsed_args, parsed_kwargs) = parse_call_method_name(call_method_name)
            if not method_args:
                method_args = parsed_args
            if not method_kwargs:
                method_kwargs = parsed_kwargs

            return_data = Return(method_name, list(method_args), method_kwargs)
            setter_method = {}

            if "=" in call_method_name:
                try:
                    setter_method = parse_kwarg(call_method_name, raise_if_unparseable=True)
                except InvalidKwargError:
                    pass

            if setter_method:
                property_name = next(iter(setter_method.keys()))
                property_value = setter_method[property_name]

                if not component._is_public(property_name):
                    raise UnicornViewError(f"'{property_name}' is not a valid property name")

                set_property_value(component, property_name, property_value)
                return_data = Return(property_name, [property_value])

            elif method_name == "$validate":
                validate_all_fields = True

            elif method_name == "$refresh":
                component = UnicornView.create(
                    component_id=component_request.id,
                    component_name=component_request.name,
                    request=request,
                )
                if component_request.data is not None:
                    for pname, pvalue in component_request.data.items():
                        set_property_from_data(component, pname, pvalue)
                component.hydrate()
                is_refresh_called = True

            elif method_name == "$reset":
                component = UnicornView.create(
                    component_id=component_request.id,
                    component_name=component_request.name,
                    request=request,
                    use_cache=False,
                )
                component.errors = {}
                is_reset_called = True

            elif method_name == "$toggle":
                for property_name in method_args:
                    property_value = _get_property_value(component, property_name)
                    property_value = not property_value
                    set_property_value(component, property_name, property_value)

            else:
                component_with_method = parent_component or component

                component_with_method.calling(method_name, method_args)
                component_method_calling.send(
                    sender=component_with_method.__class__,
                    component=component_with_method,
                    name=method_name,
                    args=method_args,
                )

                try:
                    result = _call_method_name(component_with_method, method_name, method_args, method_kwargs)

                    component_with_method.called(method_name, method_args)
                    component_method_called.send(
                        sender=component_with_method.__class__,
                        component=component_with_method,
                        method_name=method_name,
                        args=method_args,
                        kwargs=method_kwargs,
                        result=result,
                        success=True,
                        error=None,
                    )

                    if result is not None:
                        return_data.value = result
                except ValidationError as e:
                    component._handle_validation_error(e)

    component.complete()
    component_completed.send(sender=component.__class__, component=component)

    component_request.data = orjson.loads(component.get_frontend_context_variables())

    if not is_reset_called:
        updated_data = {}
        if not is_refresh_called:
            for key, value in original_data.items():
                if value != component_request.data.get(key):
                    updated_data[key] = component_request.data.get(key)
        else:
            updated_data = component_request.data

        if validate_all_fields:
            component.validate()
        else:
            component.validate(model_names=list(updated_data.keys()))

    cache_full_tree(component)

    rendered_component = component.render(request=request, epoch=component_request.epoch)
    component.rendered(rendered_component)
    component_rendered.send(
        sender=component.__class__, component=component, html=rendered_component,
    )

    response = ComponentResponse(component, component_request, return_data=return_data, partials=partials)
    result = response.get_data()

    return JsonResponse(result, json_dumps_params={"separators": (",", ":")})
