import pytest

from dk_unicorn.components import Component, UnicornView, UnicornField


class SimpleComponent(Component):
    template_name = "templates/test_component.html"
    name = "World"
    count = 0

    def increment(self):
        self.count += 1


class ExcludedComponent(Component):
    template_name = "templates/test_component.html"
    name = "World"
    secret = "hidden"

    class Meta:
        exclude = ("secret",)


class JsExcludeComponent(Component):
    template_name = "templates/test_component.html"
    name = "World"
    server_only = "private"

    class Meta:
        javascript_exclude = ("server_only",)


@pytest.fixture()
def simple_component():
    return SimpleComponent(
        component_id="test123",
        component_name="test-component",
    )


def test_component_creation(simple_component):
    assert simple_component.component_id == "test123"
    assert simple_component.component_name == "test-component"


def test_component_is_unicorn_view():
    assert UnicornView is Component


def test_component_requires_name():
    with pytest.raises(AssertionError, match="Component name is required"):
        Component(component_id="abc", component_name="")


def test_component_requires_id():
    with pytest.raises(AssertionError, match="Component id is required"):
        Component(component_id="", component_name="test")


def test_attribute_names(simple_component):
    names = simple_component._attribute_names_cache
    assert "name" in names
    assert "count" in names


def test_attributes(simple_component):
    attrs = simple_component._attributes()
    assert attrs["name"] == "World"
    assert attrs["count"] == 0


def test_methods(simple_component):
    methods = simple_component._methods()
    assert "increment" in methods
    assert callable(methods["increment"])


def test_protected_names_excluded(simple_component):
    attrs = simple_component._attributes()
    methods = simple_component._methods()
    all_public = {**attrs, **methods}
    assert "mount" not in all_public
    assert "hydrate" not in all_public
    assert "render" not in all_public
    assert "request" not in all_public
    assert "component_id" not in all_public
    assert "component_name" not in all_public
    assert "parent" not in all_public
    assert "children" not in all_public
    assert "errors" not in all_public
    assert "calls" not in all_public
    assert "force_render" not in all_public


def test_private_names_excluded(simple_component):
    attrs = simple_component._attributes()
    for name in attrs:
        assert not name.startswith("_")


def test_meta_exclude():
    comp = ExcludedComponent(
        component_id="exc1",
        component_name="excluded-comp",
    )
    attrs = comp._attributes()
    assert "name" in attrs
    assert "secret" not in attrs


def test_meta_javascript_exclude():
    comp = JsExcludeComponent(
        component_id="jsexc1",
        component_name="js-exclude-comp",
    )
    attrs = comp._attributes()
    assert "server_only" in attrs

    frontend_json = comp.get_frontend_context_variables()
    assert "server_only" not in frontend_json
    assert "name" in frontend_json


def test_lifecycle_hooks_exist(simple_component):
    assert hasattr(simple_component, "mount")
    assert hasattr(simple_component, "hydrate")
    assert hasattr(simple_component, "complete")
    assert hasattr(simple_component, "rendered")
    assert hasattr(simple_component, "parent_rendered")
    assert hasattr(simple_component, "updating")
    assert hasattr(simple_component, "updated")
    assert hasattr(simple_component, "resolved")
    assert hasattr(simple_component, "calling")
    assert hasattr(simple_component, "called")
    assert hasattr(simple_component, "pre_parse")
    assert hasattr(simple_component, "post_parse")


def test_lifecycle_hooks_callable(simple_component):
    simple_component.mount()
    simple_component.hydrate()
    simple_component.complete()
    simple_component.rendered("<div></div>")
    simple_component.parent_rendered("<div></div>")
    simple_component.updating("name", "new")
    simple_component.updated("name", "new")
    simple_component.resolved("name", "new")
    simple_component.calling("increment", [])
    simple_component.called("increment", [])
    simple_component.pre_parse()
    simple_component.post_parse()


class _ResettableField(UnicornField):
    value = "initial"


class _ResettableComponent(Component):
    template_name = "templates/test_component.html"
    field = _ResettableField()


def test_component_reset():
    comp = _ResettableComponent(
        component_id="reset1",
        component_name="resettable",
    )
    comp.field.value = "changed"
    comp.reset()
    assert comp.field.value == "initial"


def test_component_call(simple_component):
    simple_component.call("Unicorn.doSomething", "arg1", "arg2")
    assert len(simple_component.calls) == 1
    assert simple_component.calls[0]["fn"] == "Unicorn.doSomething"
    assert simple_component.calls[0]["args"] == ("arg1", "arg2")


def test_component_call_blocked():
    comp = SimpleComponent(
        component_id="block1",
        component_name="blocked",
    )
    comp.call("malicious.function", "arg")
    assert len(comp.calls) == 0


def test_component_call_allowed():
    comp = SimpleComponent(
        component_id="allow1",
        component_name="allowed",
    )
    comp.call("Unicorn.notify")
    assert len(comp.calls) == 1


def test_component_remove(simple_component):
    simple_component.remove()
    assert len(simple_component.calls) == 1
    assert simple_component.calls[0]["fn"] == "Unicorn.deleteComponent"


def test_get_frontend_context_variables(simple_component):
    result = simple_component.get_frontend_context_variables()
    assert isinstance(result, str)
    assert "name" in result
    assert "World" in result
    assert "count" in result


def test_component_cache_key(simple_component):
    assert simple_component.component_cache_key == "unicorn:component:test123"


def test_component_default_template_name():
    comp = Component(
        component_id="tpl1",
        component_name="hello-world",
    )
    assert comp.template_name == "unicorn/hello-world.html"


def test_component_custom_template_name():
    class CustomTemplate(Component):
        template_name = "templates/test_component.html"

    comp = CustomTemplate(
        component_id="tpl2",
        component_name="custom",
    )
    assert comp.template_name == "templates/test_component.html"


def test_component_parent_child():
    parent = SimpleComponent(
        component_id="parent1",
        component_name="parent",
    )
    child = SimpleComponent(
        component_id="child1",
        component_name="child",
        parent=parent,
    )
    assert child.parent is parent
    assert child in parent.children


def test_set_property(simple_component):
    simple_component._set_property("name", "Alice")
    assert simple_component.name == "Alice"


def test_set_property_with_updating_hook():
    class HookComponent(Component):
        template_name = "templates/test_component.html"
        count = 0
        updating_called = False

        def updating_count(self, value):
            self.updating_called = True

    comp = HookComponent(
        component_id="hook1",
        component_name="hook",
    )
    comp._set_property("count", 5, call_updating_method=True)
    assert comp.count == 5
    assert comp.updating_called is True


def test_component_kwargs():
    comp = SimpleComponent(
        component_id="kw1",
        component_name="kwargs-test",
        custom_arg="value",
    )
    assert comp.component_kwargs == {"custom_arg": "value"}


def test_is_public_underscore(simple_component):
    assert simple_component._is_public("_private") is False
    assert simple_component._is_public("public_attr") is True


def test_is_public_protected_names(simple_component):
    assert simple_component._is_public("mount") is False
    assert simple_component._is_public("hydrate") is False
    assert simple_component._is_public("render") is False
    assert simple_component._is_public("request") is False
    assert simple_component._is_public("component_id") is False


def test_errors_dict_initialization(simple_component):
    assert simple_component.errors == {}


def test_component_meta_exclude_not_sequence():
    with pytest.raises(AssertionError, match="Meta.exclude should be"):
        class BadExclude(Component):
            template_name = "templates/test_component.html"
            name = "test"

            class Meta:
                exclude = "name"

        BadExclude(component_id="bad1", component_name="bad")
