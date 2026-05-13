from unittest.mock import MagicMock, patch

import pytest
from django import forms

from dk_unicorn.cacher import (
    CacheableComponent,
    PointerUnicornView,
    cache_full_tree,
    restore_from_cache,
)
from dk_unicorn.components import UnicornView
from dk_unicorn.errors import UnicornCacheError


class _CacheTestComponent(UnicornView):
    template_name = "templates/test_component.html"
    name = "World"

    def get_name(self):
        return self.name


class TestPointerUnicornView:
    def test_has_component_cache_key(self):
        p = PointerUnicornView("unicorn:component:abc")
        assert p.component_cache_key == "unicorn:component:abc"

    def test_has_parent_and_children(self):
        p = PointerUnicornView("key")
        assert p.parent is None
        assert p.children == []


class TestCacheableComponent:
    def test_request_is_none_then_restored(self):
        c = _CacheTestComponent(component_id="cache-req-1", component_name="test")
        request = c.request = MagicMock()
        assert c.request

        with CacheableComponent(c):
            assert c.request is None

        assert c.request == request

    def test_extra_context_is_none_then_restored(self):
        c = _CacheTestComponent(component_id="cache-ctx-1", component_name="test")
        extra_context = c.extra_context = MagicMock()

        with CacheableComponent(c):
            assert c.extra_context is None

        assert c.extra_context == extra_context

    def test_parent_replaced_with_pointer_then_restored(self):
        parent = _CacheTestComponent(component_id="cache-parent", component_name="parent")
        child = _CacheTestComponent(component_id="cache-child", component_name="child", parent=parent)

        with CacheableComponent(child):
            assert isinstance(child.parent, PointerUnicornView)

        assert child.parent is parent

    def test_children_replaced_with_pointers_then_restored(self):
        parent = _CacheTestComponent(component_id="cache-p2", component_name="parent")
        child1 = _CacheTestComponent(component_id="cache-c1", component_name="child1", parent=parent)
        child2 = _CacheTestComponent(component_id="cache-c2", component_name="child2", parent=parent)

        with CacheableComponent(parent):
            for ch in parent.children:
                assert isinstance(ch, PointerUnicornView)

        assert child1 in parent.children
        assert child2 in parent.children

    def test_deeply_nested_parent_child_restored(self):
        grandparent = _CacheTestComponent(component_id="cache-gp", component_name="gp")
        parent = _CacheTestComponent(component_id="cache-p3", component_name="p", parent=grandparent)
        child = _CacheTestComponent(component_id="cache-c3", component_name="c", parent=parent)

        request = MagicMock()
        for c in [grandparent, parent, child]:
            c.request = request

        with CacheableComponent(child):
            assert grandparent.request is None
            assert parent.request is None
            assert child.request is None

        assert grandparent.request == request
        assert parent.request == request
        assert child.request == request


class TestCacheableComponentPickleFailure:
    def test_restores_state_on_pickle_failure(self):
        class _Unpicklable:
            def __reduce__(self):
                raise TypeError("Cannot pickle")

        class _BadComponent(UnicornView):
            template_name = "templates/test_component.html"

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.bad_attr = _Unpicklable()

        parent = _CacheTestComponent(component_id="pf-parent", component_name="parent")
        child = _BadComponent(component_id="pf-child", component_name="child", parent=parent)

        with pytest.raises(UnicornCacheError):
            with CacheableComponent(child):
                pass

        assert child.parent is parent
        assert not isinstance(child.parent, PointerUnicornView)
        assert child in parent.children


class _SimpleForm(forms.Form):
    name = forms.CharField()


class _FormComponent(UnicornView):
    template_name = "templates/test_component.html"

    def __init__(self, *args, **kwargs):
        self.form = kwargs.pop("form", None)
        super().__init__(*args, **kwargs)


class TestCacheableComponentForms:
    def test_strips_form_before_pickling(self):
        form_instance = _SimpleForm()
        c = _FormComponent(component_id="form-strip", component_name="fcomp", form=form_instance)
        assert c.form is form_instance

        with CacheableComponent(c):
            assert c.form is None

        assert c.form is form_instance


class TestCacheFullTree:
    def test_cache_and_restore(self, settings):
        settings.CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test-cache-full-tree",
            }
        }
        settings.UNICORN = {**settings.UNICORN, "CACHE_ALIAS": "default"}

        root = _CacheTestComponent(component_id="cft-root", component_name="root")
        child1 = _CacheTestComponent(component_id="cft-child1", component_name="child1", parent=root)
        child2 = _CacheTestComponent(component_id="cft-child2", component_name="child2", parent=root)

        cache_full_tree(root)

        request = MagicMock()
        restored = restore_from_cache(child1.component_cache_key, request)
        assert restored is not None
        assert restored.component_id == "cft-child1"

    def test_restore_rebuilds_tree(self, settings):
        settings.CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test-cache-tree-rebuild",
            }
        }
        settings.UNICORN = {**settings.UNICORN, "CACHE_ALIAS": "default"}

        root = _CacheTestComponent(component_id="ct-root", component_name="root")
        child1 = _CacheTestComponent(component_id="ct-child1", component_name="child1", parent=root)
        child2 = _CacheTestComponent(component_id="ct-child2", component_name="child2", parent=root)
        grandchild = _CacheTestComponent(component_id="ct-gc1", component_name="gc1", parent=child1)

        cache_full_tree(root)

        request = MagicMock()
        restored = restore_from_cache(child2.component_cache_key, request)

        restored_root = restored
        while restored_root.parent:
            restored_root = restored_root.parent

        assert restored_root.component_id == "ct-root"
        assert len(restored_root.children) == 2

    def test_restore_returns_none_for_missing_key(self, settings):
        settings.CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test-cache-missing",
            }
        }
        settings.UNICORN = {**settings.UNICORN, "CACHE_ALIAS": "default"}

        result = restore_from_cache("unicorn:component:nonexistent")
        assert result is None


class TestComponentCreateCache:
    def test_create_caches_component(self, settings):
        settings.CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test-create-cache",
            }
        }
        settings.UNICORN = {**settings.UNICORN, "CACHE_ALIAS": "default"}

        from dk_unicorn.components.unicorn_view import constructed_views_cache
        constructed_views_cache.clear()

        comp = UnicornView.create(
            component_id="cc-test1",
            component_name="tests.views.fake_components.FakeComponent",
        )
        assert comp.component_id == "cc-test1"

        comp2 = UnicornView.create(
            component_id="cc-test1",
            component_name="tests.views.fake_components.FakeComponent",
        )
        assert comp2.component_id == "cc-test1"

    def test_create_use_cache_false(self, settings):
        settings.CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test-no-cache",
            }
        }
        settings.UNICORN = {**settings.UNICORN, "CACHE_ALIAS": "default"}

        from dk_unicorn.components.unicorn_view import constructed_views_cache
        constructed_views_cache.clear()

        comp = UnicornView.create(
            component_id="nc-test1",
            component_name="tests.views.fake_components.FakeComponent",
        )
        comp.method_count = 99

        comp2 = UnicornView.create(
            component_id="nc-test1",
            component_name="tests.views.fake_components.FakeComponent",
            use_cache=False,
        )
        assert comp2.method_count == 0
