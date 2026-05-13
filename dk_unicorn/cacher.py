import logging
import pickle

from django.core.cache import caches
from django.forms import BaseForm

from dk_unicorn.errors import UnicornCacheError
from dk_unicorn.settings import get_cache_alias
from dk_unicorn.utils import create_template

logger = logging.getLogger(__name__)


class PointerUnicornView:
    def __init__(self, component_cache_key):
        self.component_cache_key = component_cache_key
        self.parent = None
        self.children = []


class CacheableComponent:
    def __init__(self, component):
        self._state = {}
        self.cacheable_component = component

    def __enter__(self):
        components = [self.cacheable_component]

        while components:
            component = components.pop()

            if component.component_id in self._state:
                continue

            extra_context = getattr(component, "extra_context", None)
            if extra_context is not None:
                component.extra_context = None

            request = component.request
            component.request = None

            template_name = component.template_name
            if not isinstance(component.template_name, str):
                component.template_name = None

            form_attributes = {}
            for attr_name, attr_val in list(vars(component).items()):
                if isinstance(attr_val, BaseForm):
                    form_attributes[attr_name] = attr_val
                    setattr(component, attr_name, None)

            self._state[component.component_id] = (
                component,
                request,
                extra_context,
                component.parent,
                component.children.copy(),
                template_name,
                form_attributes,
            )

            if component.parent:
                components.append(component.parent)
                component.parent = PointerUnicornView(component.parent.component_cache_key)

            for index, child in enumerate(component.children):
                components.append(child)
                component.children[index] = PointerUnicornView(child.component_cache_key)

        try:
            for component, *_ in self._state.values():
                pickle.dumps(component)
        except (TypeError, AttributeError, NotImplementedError, pickle.PicklingError) as e:
            self.__exit__(None, None, None)
            raise UnicornCacheError(
                f"Cannot cache component '{type(component)}' because it is not picklable: {type(e)}: {e}"
            ) from e

        return self

    def __exit__(self, *args):
        for component, request, extra_context, parent, children, template_name, form_attributes in self._state.values():
            component.request = request
            component.parent = parent
            component.children = children
            component.template_name = template_name

            for attr_name, attr_val in form_attributes.items():
                setattr(component, attr_name, attr_val)

            if component.template_name is None and hasattr(component, "template_html"):
                component.template_name = create_template(component.template_html)

            if extra_context:
                component.extra_context = extra_context

    def components(self):
        return [component for component, *_ in self._state.values()]


def cache_full_tree(component):
    root = component
    while root.parent:
        root = root.parent

    cache = caches[get_cache_alias()]

    with CacheableComponent(root) as caching:
        for _component in caching.components():
            cache.set(_component.component_cache_key, _component)


def restore_from_cache(component_cache_key, request=None):
    cache = caches[get_cache_alias()]
    cached_component = cache.get(component_cache_key)

    if cached_component:
        roots = {}
        root = cached_component
        roots[root.component_cache_key] = root

        while root.parent:
            root = cache.get(root.parent.component_cache_key)
            roots[root.component_cache_key] = root

        to_traverse = [root]

        while to_traverse:
            current = to_traverse.pop()
            if request:
                current.setup(request)
            current._validate_called = False
            current.calls = []

            for index, child in enumerate(current.children):
                key = child.component_cache_key
                cached_child = roots.pop(key, None) or cache.get(key)
                cached_child.parent = current
                current.children[index] = cached_child
                to_traverse.append(cached_child)

    return cached_component
