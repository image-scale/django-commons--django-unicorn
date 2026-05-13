import dataclasses
from typing import Optional

import pytest

from dk_unicorn.components import UnicornField, UnicornView
from dk_unicorn.views.utils import set_property_from_data, _is_component_field_model_or_unicorn_field


class SimpleComponent(UnicornView):
    template_name = "test.html"
    name: str = "default"
    count: int = 0
    active: bool = True
    _private: str = "hidden"


class AuthorField(UnicornField):
    name: str = "Unknown"
    age: int = 0


class ComponentWithField(UnicornView):
    template_name = "test.html"
    author: AuthorField = None

    def mount(self):
        self.author = AuthorField()


@dataclasses.dataclass
class Point:
    x: int = 0
    y: int = 0


class ComponentWithDataclass(UnicornView):
    template_name = "test.html"
    point: Point = None

    def mount(self):
        self.point = Point()


def test_set_simple_property():
    c = SimpleComponent(component_name="test", component_id="123")
    set_property_from_data(c, "name", "Alice")
    assert c.name == "Alice"


def test_set_int_property():
    c = SimpleComponent(component_name="test", component_id="123")
    set_property_from_data(c, "count", "5")
    assert c.count == 5


def test_set_bool_property():
    c = SimpleComponent(component_name="test", component_id="123")
    set_property_from_data(c, "active", False)
    assert c.active is False


def test_skip_missing_property():
    c = SimpleComponent(component_name="test", component_id="123")
    set_property_from_data(c, "nonexistent", "value")
    assert not hasattr(c, "nonexistent")


def test_skip_private_property():
    c = SimpleComponent(component_name="test", component_id="123")
    set_property_from_data(c, "_private", "hacked")
    assert c._private == "hidden"


def test_set_unicorn_field_nested():
    c = ComponentWithField(component_name="test", component_id="123")
    c.mount()
    set_property_from_data(c, "author", {"name": "Bob", "age": 42})
    assert c.author.name == "Bob"
    assert c.author.age == 42


def test_unicorn_field_detection():
    c = ComponentWithField(component_name="test", component_id="123")
    c.mount()
    assert _is_component_field_model_or_unicorn_field(c, "author") is True


def test_non_field_detection():
    c = SimpleComponent(component_name="test", component_id="123")
    assert _is_component_field_model_or_unicorn_field(c, "name") is False


def test_set_property_type_casts():
    c = SimpleComponent(component_name="test", component_id="123")
    set_property_from_data(c, "count", "42")
    assert c.count == 42
    assert isinstance(c.count, int)


class NullableFieldComponent(UnicornView):
    template_name = "test.html"
    author: Optional[AuthorField] = None


def test_nullable_field_auto_instantiated():
    c = NullableFieldComponent(component_name="test", component_id="123")
    assert c.author is None
    result = _is_component_field_model_or_unicorn_field(c, "author")
    assert result is True
    assert c.author is not None


@pytest.mark.django_db
def test_set_model_property():
    from example.coffee.models import Flavor

    class ModelComponent(UnicornView):
        template_name = "test.html"
        flavor: Flavor = None

        def mount(self):
            self.flavor = Flavor(name="Test", label="test")
            self.flavor.save()

    c = ModelComponent(component_name="test", component_id="123")
    c.mount()

    assert _is_component_field_model_or_unicorn_field(c, "flavor") is True

    set_property_from_data(c, "flavor", {"name": "Updated", "label": "updated"})
    assert c.flavor.name == "Updated"


def test_set_dataclass_property():
    c = ComponentWithDataclass(component_name="test", component_id="123")
    c.mount()
    set_property_from_data(c, "point", {"x": 10, "y": 20})
    assert c.point.x == 10
    assert c.point.y == 20


class ListComponent(UnicornView):
    template_name = "test.html"
    items: list = None

    def mount(self):
        self.items = [1, 2, 3]


def test_set_list_property():
    c = ListComponent(component_name="test", component_id="123")
    c.mount()
    set_property_from_data(c, "items", [4, 5, 6])
    assert c.items == [4, 5, 6]


class DictComponent(UnicornView):
    template_name = "test.html"
    data: dict = None

    def mount(self):
        self.data = {"key": "val"}


def test_set_dict_property():
    c = DictComponent(component_name="test", component_id="123")
    c.mount()
    set_property_from_data(c, "data", {"new_key": "new_val"})
    assert c.data == {"new_key": "new_val"}


def test_ignore_m2m():
    c = SimpleComponent(component_name="test", component_id="123")
    set_property_from_data(c, "name", "test", ignore_m2m=True)
    assert c.name == "test"
