import pytest

from dk_unicorn.components.unicorn_view import (
    get_locations,
    to_snake_case,
    to_dash_case,
    to_pascal_case,
    Component,
)
from dk_unicorn.errors import ComponentModuleLoadError


def setup_function():
    get_locations.cache_clear()


def test_to_snake_case():
    assert to_snake_case("hello-world") == "hello_world"


def test_to_dash_case():
    assert to_dash_case("hello_world") == "hello-world"


def test_to_pascal_case():
    assert to_pascal_case("hello-world") == "HelloWorld"
    assert to_pascal_case("hello_world") == "HelloWorld"


def test_get_locations_simple():
    locations = get_locations("hello-world")
    assert len(locations) >= 1
    found_class_names = [loc[1] for loc in locations]
    assert "HelloWorldView" in found_class_names


def test_get_locations_dotted():
    locations = get_locations("nested.my-component")
    found_class_names = [loc[1] for loc in locations]
    assert any("MyComponent" in name for name in found_class_names)


def test_get_locations_fully_qualified():
    locations = get_locations("myapp.components.MyView")
    assert locations[0] == ("myapp.components", "MyView")


def test_get_locations_with_component_suffix():
    locations = get_locations("myapp.components.MyComponent")
    assert locations[0] == ("myapp.components", "MyComponent")
    assert len(locations) == 1


def test_create_raises_module_not_found():
    with pytest.raises(ComponentModuleLoadError):
        Component.create(
            component_id="test1",
            component_name="nonexistent-component",
        )


def test_create_requires_id():
    with pytest.raises(AssertionError, match="Component id is required"):
        Component.create(component_id="", component_name="test")


def test_create_requires_name():
    with pytest.raises(AssertionError, match="Component name is required"):
        Component.create(component_id="test1", component_name="")


def test_create_rejects_path_traversal():
    with pytest.raises(AssertionError, match="Invalid component name"):
        Component.create(component_id="test1", component_name="../etc/passwd")
