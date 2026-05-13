import pytest
from django.template import Template, Context


def test_unicorn_scripts():
    template = Template("{% load unicorn %}{% unicorn_scripts %}")
    rendered = template.render(Context({}))
    assert "script" in rendered


def test_unicorn_errors_no_errors():
    template = Template("{% load unicorn %}{% unicorn_errors %}")
    context = Context({"unicorn": {"errors": {}}})
    rendered = template.render(context)
    assert "unicorn-errors" not in rendered


def test_unicorn_errors_with_errors():
    template = Template("{% load unicorn %}{% unicorn_errors %}")
    context = Context({
        "unicorn": {
            "errors": {
                "field1": [{"code": "required", "message": "This field is required"}]
            }
        }
    })
    rendered = template.render(context)
    assert "unicorn-errors" in rendered
    assert "This field is required" in rendered


def test_unicorn_tag_requires_argument():
    with pytest.raises(Exception):
        Template("{% load unicorn %}{% unicorn %}")
