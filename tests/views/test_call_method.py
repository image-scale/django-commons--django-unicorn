from typing import Optional
from unittest.mock import MagicMock

import pytest

from dk_unicorn.components import UnicornView
from dk_unicorn.views import _call_method_name


class TypedComponent(UnicornView):
    template_name = "test.html"
    result = None

    def typed_int(self, val: int):
        self.result = val
        return val

    def typed_optional(self, val: Optional[int] = None):
        self.result = val
        return val

    def typed_str(self, name: str = "default"):
        self.result = name
        return name

    def no_hints(self, val):
        self.result = val
        return val


def test_call_with_int_cast():
    c = TypedComponent(component_name="test", component_id="123")
    result = _call_method_name(c, "typed_int", ("42",), {})
    assert result == 42


def test_call_with_optional_int():
    c = TypedComponent(component_name="test", component_id="123")
    result = _call_method_name(c, "typed_optional", ("7",), {})
    assert result == 7


def test_call_with_optional_none():
    c = TypedComponent(component_name="test", component_id="123")
    result = _call_method_name(c, "typed_optional", (None,), {})
    assert result is None


def test_call_with_kwargs():
    c = TypedComponent(component_name="test", component_id="123")
    result = _call_method_name(c, "typed_str", (), {"name": "hello"})
    assert result == "hello"


def test_call_no_type_hints():
    c = TypedComponent(component_name="test", component_id="123")
    result = _call_method_name(c, "no_hints", ("raw",), {})
    assert result == "raw"


@pytest.mark.django_db
def test_call_with_model_arg():
    from example.coffee.models import Flavor

    class ModelArgComponent(UnicornView):
        template_name = "test.html"
        result = None

        def lookup_flavor(self, flavor: Flavor):
            self.result = flavor
            return flavor.name

    f = Flavor(name="TestFlavor", label="test")
    f.save()

    c = ModelArgComponent(component_name="test", component_id="123")
    result = _call_method_name(c, "lookup_flavor", (f.pk,), {})
    assert result == "TestFlavor"
    assert c.result.pk == f.pk


@pytest.mark.django_db
def test_call_with_model_kwarg():
    from example.coffee.models import Flavor

    class ModelKwargComponent(UnicornView):
        template_name = "test.html"

        def lookup_flavor(self, flavor: Flavor):
            return flavor.name

    f = Flavor(name="KwargFlavor", label="kwarg")
    f.save()

    c = ModelKwargComponent(component_name="test", component_id="123")
    result = _call_method_name(c, "lookup_flavor", (), {"pk": f.pk})
    assert result == "KwargFlavor"


def test_call_nonexistent_method():
    c = TypedComponent(component_name="test", component_id="123")
    result = _call_method_name(c, "nonexistent", (), {})
    assert result is None
