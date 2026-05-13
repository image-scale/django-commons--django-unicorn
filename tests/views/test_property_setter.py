import pytest

from dk_unicorn.components import Component, UnicornField
from dk_unicorn.errors import UnicornViewError
from dk_unicorn.views.property_setter import set_property_value


class _Author(UnicornField):
    name = "Neil"
    age = 50


class _SimpleComponent(Component):
    template_name = "templates/test_component.html"
    name = "World"
    count = 0
    active = True
    author = _Author()
    items = {"x": 1, "y": 2}
    numbers = [10, 20, 30]

    class Meta:
        exclude = ("secret",)

    secret = "hidden"


def _make_component():
    return _SimpleComponent(component_id="prop-test-1", component_name="prop-test")


class TestSetPropertyValueSimple:
    def test_set_simple_string(self):
        c = _make_component()
        set_property_value(c, "name", "Alice")
        assert c.name == "Alice"

    def test_set_simple_int(self):
        c = _make_component()
        set_property_value(c, "count", 42)
        assert c.count == 42

    def test_set_bool(self):
        c = _make_component()
        set_property_value(c, "active", False)
        assert c.active is False


class TestSetPropertyValueNested:
    def test_nested_dot_notation(self):
        c = _make_component()
        set_property_value(c, "author.name", "Gaiman")
        assert c.author.name == "Gaiman"

    def test_dict_dot_notation(self):
        c = _make_component()
        set_property_value(c, "items.x", 99, data={"items": {"x": 1, "y": 2}})
        assert c.items["x"] == 99

    def test_list_dot_notation(self):
        c = _make_component()
        set_property_value(c, "numbers.1", 77)
        assert c.numbers[1] == 77


class TestSetPropertyValueAccessControl:
    def test_rejects_private_property(self):
        c = _make_component()
        with pytest.raises(UnicornViewError, match="not a valid property"):
            set_property_value(c, "_hidden", "bad")

    def test_rejects_excluded_property(self):
        c = _make_component()
        with pytest.raises(UnicornViewError, match="not a valid property"):
            set_property_value(c, "secret", "exposed")

    def test_rejects_dunder(self):
        c = _make_component()
        with pytest.raises(UnicornViewError, match="not a valid property"):
            set_property_value(c, "__init__", "bad")

    def test_rejects_none_name(self):
        c = _make_component()
        with pytest.raises(AssertionError, match="Property name is required"):
            set_property_value(c, None, "bad")

    def test_rejects_none_value(self):
        c = _make_component()
        with pytest.raises(AssertionError, match="Property value is required"):
            set_property_value(c, "name", None)


class TestSetPropertyValueLifecycle:
    def test_calls_updating_hook(self):
        calls = []

        class _HookComponent(Component):
            template_name = "templates/test_component.html"
            color = "red"

            def updating(self, name, value):
                calls.append(("updating", name, value))

            def updated(self, name, value):
                calls.append(("updated", name, value))

        c = _HookComponent(component_id="hook1", component_name="hook-test")
        set_property_value(c, "color", "blue")
        assert c.color == "blue"
        assert ("updating", "color", "blue") in calls
        assert ("updated", "color", "blue") in calls

    def test_fires_signals(self):
        from dk_unicorn.signals import component_property_updating, component_property_updated

        results = []

        def on_updating(sender, **kwargs):
            results.append("updating")

        def on_updated(sender, **kwargs):
            results.append("updated")

        component_property_updating.connect(on_updating)
        component_property_updated.connect(on_updated)

        try:
            c = _make_component()
            set_property_value(c, "name", "Signal")
            assert "updating" in results
            assert "updated" in results
        finally:
            component_property_updating.disconnect(on_updating)
            component_property_updated.disconnect(on_updated)

    def test_call_resolved_false(self):
        resolved_calls = []

        class _ResolveComponent(Component):
            template_name = "templates/test_component.html"
            color = "red"

            def resolved_color(self, value):
                resolved_calls.append(value)

        c = _ResolveComponent(component_id="res1", component_name="resolve-test")
        set_property_value(c, "color", "green", call_resolved_method=False)
        assert c.color == "green"
        assert resolved_calls == []
