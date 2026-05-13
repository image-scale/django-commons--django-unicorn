import copy
import logging
from functools import wraps

import orjson
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
from dk_unicorn.typer import cast_value, get_type_hints
from dk_unicorn.utils import get_method_arguments
from dk_unicorn.views.action import CallMethod, Refresh, Reset, SyncInput, Toggle
from dk_unicorn.views.property_setter import set_property_value
from dk_unicorn.views.request import ComponentRequest
from dk_unicorn.views.response import ComponentResponse

logger = logging.getLogger(__name__)


def _set_property_from_data(component, name, value):
    try:
        if not hasattr(component, name):
            return
        if not component._is_public(name):
            return
    except ValueError:
        return

    if hasattr(component, "_set_property"):
        component._set_property(name, value, call_updating_method=True, call_updated_method=False)
    else:
        setattr(component, name, value)


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

                if not isinstance(type_hint, type):
                    continue

                if argument in kwargs:
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
        _set_property_from_data(component, property_name, property_value)

    component.post_parse()
    component_post_parsed.send(sender=component.__class__, component=component)

    component.hydrate()
    component_hydrated.send(sender=component.__class__, component=component)

    is_reset_called = False
    is_refresh_called = False
    validate_all_fields = False
    return_data = None
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
                _set_property_from_data(component, pname, pvalue)
            component.hydrate()
            is_refresh_called = True

        elif isinstance(action, Toggle):
            for property_name in action.args:
                property_value = _get_property_value(component, property_name)
                property_value = not property_value
                set_property_value(component, property_name, property_value)

        elif isinstance(action, CallMethod):
            component.calling(action.method_name, action.args)
            component_method_calling.send(
                sender=component.__class__,
                component=component,
                name=action.method_name,
                args=action.args,
            )

            try:
                result = _call_method_name(component, action.method_name, action.args, action.kwargs)

                component.called(action.method_name, action.args)
                component_method_called.send(
                    sender=component.__class__,
                    component=component,
                    method_name=action.method_name,
                    args=action.args,
                    kwargs=action.kwargs,
                    result=result,
                    success=True,
                    error=None,
                )

                if result is not None:
                    return_data = {"value": result}
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
