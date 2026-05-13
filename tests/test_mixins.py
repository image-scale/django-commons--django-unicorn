import pytest

from dk_unicorn.components.mixins import ModelValueMixin


class NonModelMixin(ModelValueMixin):
    pass


def test_mixin_non_model_returns_empty():
    obj = NonModelMixin()
    assert obj.value() == {}


@pytest.mark.django_db
def test_mixin_value_on_model_instance():
    from example.coffee.models import Flavor

    f = Flavor(name="Mocha", label="mocha")
    f.save()

    result = ModelValueMixin.value(f)
    assert result["name"] == "Mocha"
    assert result["label"] == "mocha"
    assert result["pk"] == f.pk


@pytest.mark.django_db
def test_mixin_value_with_fields_filter():
    from example.coffee.models import Flavor

    f = Flavor(name="Latte", label="latte")
    f.save()

    result = ModelValueMixin.value(f, "name", "pk")
    assert "name" in result
    assert "pk" in result
    assert "label" not in result
