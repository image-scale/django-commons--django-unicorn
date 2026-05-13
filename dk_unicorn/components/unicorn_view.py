import importlib
import inspect
import logging
import pickle
from collections.abc import Callable, Sequence
from functools import lru_cache
from typing import Any, Optional, cast

from django.apps import apps as django_apps_module
from django.db.models import Model
from django.http import HttpRequest, HttpResponseRedirect
from django.views.generic.base import TemplateView

from dk_unicorn import serializer
from dk_unicorn.cacher import cache_full_tree, restore_from_cache
from dk_unicorn.components.fields import UnicornField
from dk_unicorn.components.template_response import ComponentTemplateResponse
from dk_unicorn.errors import (
    ComponentClassLoadError,
    ComponentModuleLoadError,
    UnicornCacheError,
)
from dk_unicorn.settings import get_setting
from dk_unicorn.signals import (
    component_completed,
    component_hydrated,
    component_mounted,
)
from dk_unicorn.utils import create_template, is_non_string_sequence

logger = logging.getLogger(__name__)

try:
    from cachetools.lru import LRUCache
except ImportError:
    from cachetools import LRUCache

constructed_views_cache = LRUCache(maxsize=100)

STANDARD_KWARG_KEYS = {
    "id",
    "component_id",
    "component_name",
    "component_key",
    "parent",
    "request",
}

PROTECTED_NAMES = (
    "render",
    "request",
    "args",
    "kwargs",
    "content_type",
    "extra_context",
    "http_method_names",
    "template_engine",
    "template_name",
    "template_html",
    "dispatch",
    "id",
    "get",
    "get_context_data",
    "get_template_names",
    "render_to_response",
    "http_method_not_allowed",
    "options",
    "setup",
    "fill",
    "view_is_async",
    "component_id",
    "component_name",
    "component_key",
    "reset",
    "mount",
    "hydrate",
    "updating",
    "update",
    "calling",
    "called",
    "complete",
    "rendered",
    "parent_rendered",
    "validate",
    "is_valid",
    "get_frontend_context_variables",
    "errors",
    "updated",
    "resolved",
    "parent",
    "children",
    "call",
    "remove",
    "calls",
    "component_cache_key",
    "component_kwargs",
    "component_args",
    "force_render",
    "pre_parse",
    "post_parse",
    "login_not_required",
    "form_class",
)


def to_snake_case(s):
    return s.replace("-", "_")


def to_dash_case(s):
    return s.replace("_", "-")


def to_pascal_case(s):
    s = to_snake_case(s)
    return "".join(word.title() for word in s.split("_"))


@lru_cache(maxsize=128, typed=True)
def get_locations(component_name):
    locations = []

    if "." in component_name:
        component_name = component_name.replace("/", ".")
        class_name = component_name.split(".")[-1]
        module_name = component_name.replace(f".{class_name}", "")
        locations.append((module_name, class_name))

        if component_name.endswith("View") or component_name.endswith("Component"):
            return locations

    component_name = component_name.replace("/", ".")
    class_name = to_pascal_case(component_name)

    if "." in class_name:
        parts = class_name.split(".")
        if parts[-1]:
            class_name = parts[-1]

    class_name = f"{class_name}View"
    module_name = to_snake_case(component_name)

    all_django_apps = [app_config.name for app_config in django_apps_module.get_app_configs()]
    unicorn_apps = get_setting("APPS", all_django_apps)

    if not is_non_string_sequence(unicorn_apps):
        raise AssertionError("APPS is expected to be a list, tuple or set")

    locations += [(f"{app}.components.{module_name}", class_name) for app in unicorn_apps]
    locations.append((f"components.{module_name}", class_name))

    return locations


def build_component(
    component_class,
    component_id,
    component_name,
    component_key,
    parent,
    request,
    component_args,
    **kwargs,
):
    component = component_class(
        component_id=component_id,
        component_name=component_name,
        component_key=component_key,
        parent=parent,
        request=request,
        component_args=component_args,
        **kwargs,
    )

    component.calls = []
    component._mount_result = component.mount()
    component_mounted.send(sender=component.__class__, component=component)
    component.hydrate()
    component_hydrated.send(sender=component.__class__, component=component)
    component.complete()
    component_completed.send(sender=component.__class__, component=component)
    component._validate_called = False

    return component


class Component(TemplateView):
    component_name: str = ""
    component_key: str = ""
    component_id: str = ""
    component_args: list | None = None
    component_kwargs: dict | None = None

    def __init__(self, component_args=None, **kwargs):
        self.response_class = ComponentTemplateResponse

        self.component_name = kwargs.get("component_name", "")
        self.component_key = ""
        self.component_id = ""

        self.request = HttpRequest()
        self.parent = None
        self.children = []

        self._methods_cache = {}
        self._attribute_names_cache = []
        self._hook_methods_cache = []
        self._resettable_attributes_cache = {}

        self.calls = []
        self.force_render = False

        super().__init__(**kwargs)

        if not self.component_name:
            raise AssertionError("Component name is required")

        if kwargs.get("id"):
            self.component_id = kwargs["id"]

        if not self.component_id:
            raise AssertionError("Component id is required")

        self.component_cache_key = f"unicorn:component:{self.component_id}"

        if "request" in kwargs:
            self.setup(kwargs["request"])

        if "parent" in kwargs:
            self.parent = kwargs["parent"]
            if self.parent and self not in self.parent.children:
                self.parent.children.append(self)

        self.component_args = component_args if component_args is not None else []

        custom_kwargs = set(kwargs.keys()) - STANDARD_KWARG_KEYS
        self.component_kwargs = {k: kwargs[k] for k in list(custom_kwargs)}

        self._init_script = ""
        self._validate_called = False
        self.errors = {}

        if not self.component_key and hasattr(self, "Meta") and hasattr(self.Meta, "component_key"):
            self.component_key = self.Meta.component_key

        self._set_default_template_name()
        self._set_caches()

    def _set_default_template_name(self):
        template_html = None
        if hasattr(self, "Meta") and hasattr(self.Meta, "template_html"):
            template_html = self.Meta.template_html
        elif hasattr(self, "template_html"):
            template_html = self.template_html

        if template_html:
            try:
                self.template_name = create_template(template_html)
            except AssertionError:
                pass
        elif hasattr(self, "Meta") and hasattr(self.Meta, "template_name"):
            self.template_name = self.Meta.template_name

        get_template_names_valid = False
        try:
            self.get_template_names()
            get_template_names_valid = True
        except Exception:
            pass

        if not self.template_name and not get_template_names_valid:
            template_name = self.component_name.replace(".", "/")
            self.template_name = f"unicorn/{template_name}.html"

    def _set_caches(self):
        self._attribute_names_cache = self._attribute_names()
        self._set_hook_methods_cache()
        self._methods_cache = self._methods()
        self._set_resettable_attributes_cache()

    def reset(self):
        for attr_name, pickled_value in self._resettable_attributes_cache.items():
            try:
                attr_value = pickle.loads(pickled_value)  # noqa: S301
                self._set_property(attr_name, attr_value)
            except (TypeError, pickle.PickleError):
                pass

    def call(self, function_name, *args):
        allowed_list = get_setting("ALLOWED_JS_CALL_LIST", ["Unicorn"])
        root_name = function_name.split(".")[0]

        if allowed_list and root_name not in allowed_list:
            return

        self.calls.append({"fn": function_name, "args": args})

    def remove(self):
        self.call("Unicorn.deleteComponent", self.component_id)

    def mount(self):
        pass

    def hydrate(self):
        pass

    def complete(self):
        pass

    def rendered(self, html):
        pass

    def parent_rendered(self, html):
        pass

    def updating(self, name, value):
        pass

    def updated(self, name, value):
        pass

    def resolved(self, name, value):
        pass

    def calling(self, name, args):
        pass

    def called(self, name, args):
        pass

    def pre_parse(self):
        pass

    def post_parse(self):
        pass

    def get_frontend_context_variables(self):
        frontend_vars = {}
        attributes = self._attributes()
        frontend_vars.update(attributes)

        exclude_field_attributes = []

        if hasattr(self, "Meta") and hasattr(self.Meta, "javascript_exclude"):
            if isinstance(self.Meta.javascript_exclude, Sequence):
                for field_name in self.Meta.javascript_exclude:
                    field_name = cast(str, field_name)
                    if "." in field_name:
                        exclude_field_attributes.append(field_name)
                    else:
                        if field_name not in frontend_vars:
                            raise serializer.InvalidFieldNameError(
                                field_name=field_name,
                                data=cast(dict, frontend_vars),
                            )
                        del frontend_vars[field_name]

        from django.forms import BaseForm
        for field_name in list(frontend_vars.keys()):
            if isinstance(frontend_vars[field_name], BaseForm):
                del frontend_vars[field_name]

        return serializer.dumps(
            frontend_vars,
            exclude_field_attributes=tuple(exclude_field_attributes) if exclude_field_attributes else None,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attributes = self._attributes()
        context.update(attributes)
        context.update(self._methods())
        context.update({
            "unicorn": {
                "component_id": self.component_id,
                "component_name": self.component_name,
                "component_key": self.component_key,
                "component": self,
                "errors": self.errors,
            }
        })
        return context

    def is_valid(self, model_names=None):
        return len(self.validate(model_names).keys()) == 0

    def _handle_validation_error(self, e):
        NON_FIELD_ERRORS = "__all__"

        if len(e.args) < 2 or not e.args[1]:
            raise AssertionError("Error code must be specified") from e

        if hasattr(e, "error_list"):
            error_code = e.args[1]
            for error in e.error_list:
                if NON_FIELD_ERRORS in self.errors:
                    self.errors[NON_FIELD_ERRORS].append({"code": error_code, "message": error.message})
                else:
                    self.errors[NON_FIELD_ERRORS] = [{"code": error_code, "message": error.message}]
        elif hasattr(e, "message_dict"):
            error_code = e.args[1]
            for field, msg in e.message_dict.items():
                if field in self.errors:
                    self.errors[field].append({"code": error_code, "message": msg})
                else:
                    self.errors[field] = [{"code": error_code, "message": msg}]

    def validate(self, model_names=None):
        if self._validate_called:
            return self.errors

        self._validate_called = True
        data = self._attributes()
        form = self._get_form(data)

        if form:
            form_errors = form.errors.get_json_data(escape_html=True)

            if self.errors:
                keys_to_remove = []
                for key, value in self.errors.items():
                    if key in form_errors:
                        self.errors[key] = value
                    else:
                        keys_to_remove.append(key)
                for key in keys_to_remove:
                    self.errors.pop(key)

            if model_names is not None:
                for key, value in form_errors.items():
                    if key in model_names:
                        self.errors[key] = value
            else:
                self.errors.update(form_errors)

        return self.errors

    def _get_form(self, data):
        form_class = None
        if hasattr(self, "Meta") and hasattr(self.Meta, "form_class"):
            form_class = self.Meta.form_class
        elif hasattr(self, "form_class"):
            form_class = self.form_class

        if form_class:
            try:
                form = form_class(data=data)
                form.is_valid()
                return form
            except Exception:
                return None

    def render(self, *, init_js=False, extra_context=None, request=None, epoch=None):
        if extra_context is not None:
            self.extra_context = extra_context

        if request:
            self.request = request

        if hasattr(self, "_mount_result") and self._mount_result:
            if isinstance(self._mount_result, HttpResponseRedirect):
                return f"<script>window.location.href = '{self._mount_result.url}';</script>"

        response = self.render_to_response(
            context=self.get_context_data(),
            component=self,
            init_js=init_js,
            epoch=epoch,
        )

        if hasattr(response, "render"):
            response.render()

        return response.content.decode("utf-8")

    def _attribute_names(self):
        non_callables = [
            member[0]
            for member in inspect.getmembers(self, lambda x: not callable(x))
        ]
        attribute_names = [name for name in non_callables if self._is_public(name)]

        try:
            from typing import get_type_hints
            hints = get_type_hints(self.__class__)
            for hint_name in hints:
                if self._is_public(hint_name) and hint_name not in attribute_names:
                    attribute_names.append(hint_name)
        except Exception:
            pass

        return attribute_names

    def _attributes(self):
        attributes = {}
        for attr_name in self._attribute_names_cache:
            attributes[attr_name] = getattr(self, attr_name, None)
        return attributes

    def _set_property(self, name, value, *, call_updating_method=False,
                      call_updated_method=False, call_resolved_method=False):
        if call_updating_method:
            updating_fn = f"updating_{name}"
            if hasattr(self, updating_fn):
                getattr(self, updating_fn)(value)

        setattr(self, name, value)

        if call_updated_method:
            updated_fn = f"updated_{name}"
            if hasattr(self, updated_fn):
                getattr(self, updated_fn)(value)

        if call_resolved_method:
            resolved_fn = f"resolved_{name}"
            if hasattr(self, resolved_fn):
                getattr(self, resolved_fn)(value)

    def _methods(self):
        if self._methods_cache:
            return self._methods_cache

        member_methods = inspect.getmembers(self, inspect.ismethod)
        public_methods = [m for m in member_methods if self._is_public(m[0])]
        methods = dict(public_methods)
        self._methods_cache = methods
        return methods

    def _set_hook_methods_cache(self):
        self._hook_methods_cache = []
        for attr_name in self._attribute_names_cache:
            for prefix in ("updating_", "updated_"):
                fn_name = f"{prefix}{attr_name}"
                if hasattr(self, fn_name):
                    self._hook_methods_cache.append(fn_name)

    def _set_resettable_attributes_cache(self):
        self._resettable_attributes_cache = {}
        for attr_name, attr_value in self._attributes().items():
            if isinstance(attr_value, UnicornField):
                self._resettable_attributes_cache[attr_name] = pickle.dumps(attr_value)
            elif isinstance(attr_value, Model):
                if not attr_value.pk:
                    try:
                        self._resettable_attributes_cache[attr_name] = pickle.dumps(attr_value)
                    except pickle.PickleError:
                        pass

    def _cache_component(self, *, parent=None, component_args=None, **kwargs):
        constructed_views_cache[self.component_id] = self

        try:
            cache_full_tree(self)
        except UnicornCacheError as e:
            logger.warning(e)

    def _is_public(self, name):
        excludes = []

        if hasattr(self, "Meta") and hasattr(self.Meta, "exclude"):
            if not is_non_string_sequence(self.Meta.exclude):
                raise AssertionError("Meta.exclude should be a list, tuple, or set")
            excludes = self.Meta.exclude

        return not (
            name.startswith("_")
            or name in PROTECTED_NAMES
            or name in self._hook_methods_cache
            or name in excludes
        )

    @staticmethod
    def create(
        *,
        component_id,
        component_name,
        component_key="",
        parent=None,
        request=None,
        use_cache=True,
        component_args=None,
        kwargs=None,
    ):
        if not component_id:
            raise AssertionError("Component id is required")
        if not component_name:
            raise AssertionError("Component name is required")
        if ".." in component_name:
            raise AssertionError("Invalid component name")

        component_args = component_args if component_args is not None else []
        kwargs = kwargs if kwargs is not None else {}

        component_cache_key = f"unicorn:component:{component_id}"
        cached_component = restore_from_cache(component_cache_key, request=request)

        if not cached_component:
            cached_component = constructed_views_cache.get(component_id)
            if cached_component:
                cached_component.setup(request)
                cached_component._validate_called = False
                cached_component.calls = []

        if use_cache and cached_component:
            cached_component.component_args = component_args
            cached_component.component_kwargs = kwargs

            if parent is not None:
                cached_component.parent = parent

            for key, value in kwargs.items():
                if hasattr(cached_component, key):
                    setattr(cached_component, key, value)

            cached_component._cache_component(parent=parent, component_args=component_args, **kwargs)

            cached_component.hydrate()
            component_hydrated.send(sender=cached_component.__class__, component=cached_component)

            return cached_component

        locations = get_locations(component_name)

        for module_name, class_name in locations:
            try:
                module = importlib.import_module(module_name)
                component_class = getattr(module, class_name, None)

                if component_class is None:
                    continue

                component = build_component(
                    component_class=component_class,
                    component_id=component_id,
                    component_name=component_name,
                    component_key=component_key,
                    parent=parent,
                    request=request,
                    component_args=component_args,
                    **kwargs,
                )

                component._cache_component(parent=parent, component_args=component_args, **kwargs)

                return component
            except ModuleNotFoundError as e:
                if str(e.name) != module_name and str(e.name) != module_name.split(".")[-1]:
                    raise ComponentModuleLoadError(
                        f"Error loading '{module_name}': {e}",
                        locations=locations,
                    ) from e
                continue
            except AttributeError:
                continue

        raise ComponentModuleLoadError(
            f"Could not find component '{component_name}'",
            locations=locations,
        )


UnicornView = Component
