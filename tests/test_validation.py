from datetime import datetime, timezone

import pytest
from django import forms
from django.forms import ValidationError

from dk_unicorn.components import Component, UnicornView
from tests.views.utils import post_and_get_response


class _ValidationForm(forms.Form):
    text = forms.CharField(min_length=3, max_length=10)
    number = forms.IntegerField()


class _ValidationComponent(Component):
    template_name = "templates/test_component.html"
    form_class = _ValidationForm
    text = "hello"
    number = ""

    def set_text_no_validation(self):
        self.text = "no validation"

    def set_text_with_validation(self):
        self.text = "validation 33"
        self.validate()

    def set_number(self, number):
        self.number = number

    def raise_dict_error(self):
        raise ValidationError({"check": "Check is required"}, code="required")

    def raise_dict_error_no_code(self):
        raise ValidationError({"check": "Check is required"})

    def raise_string_error(self):
        raise ValidationError("Check is required", code="required")

    def raise_string_error_no_code(self):
        raise ValidationError("Check is required")

    def raise_list_error(self):
        raise ValidationError(
            [ValidationError({"check": "Check is required"})],
            code="required",
        )

    def raise_list_error_no_code(self):
        raise ValidationError(
            [ValidationError({"check": "Check is required"})],
        )


def _make_component(**kwargs):
    return _ValidationComponent(component_id="val-1", component_name="val-test", **kwargs)


class TestComponentValidate:
    def test_validate_returns_errors(self):
        c = _make_component()
        c.number = ""
        errors = c.validate()
        assert "number" in errors

    def test_validate_with_model_names(self):
        c = _make_component()
        c.number = ""
        errors = c.validate(model_names=["number"])
        assert "number" in errors

    def test_validate_skips_unrequested_fields(self):
        c = _make_component()
        c.number = ""
        errors = c.validate(model_names=["text"])
        assert "number" not in errors

    def test_is_valid_true(self):
        c = _make_component()
        c.text = "hello"
        c.number = 42
        assert c.is_valid() is True

    def test_is_valid_false(self):
        c = _make_component()
        c.text = "hello"
        c.number = ""
        assert c.is_valid() is False

    def test_validate_only_called_once(self):
        c = _make_component()
        c.number = ""
        errors1 = c.validate()
        c.number = 42
        errors2 = c.validate()
        assert errors1 == errors2


class TestHandleValidationError:
    def test_dict_error(self):
        c = _make_component()
        e = ValidationError({"field": "Error msg"}, code="required")
        c._handle_validation_error(e)
        assert "field" in c.errors
        assert c.errors["field"][0]["code"] == "required"

    def test_string_error(self):
        c = _make_component()
        e = ValidationError("String error", code="required")
        c._handle_validation_error(e)
        assert "__all__" in c.errors
        assert c.errors["__all__"][0]["code"] == "required"

    def test_no_code_raises(self):
        c = _make_component()
        e = ValidationError({"field": "Error msg"})
        with pytest.raises(AssertionError, match="Error code must be specified"):
            c._handle_validation_error(e)


class TestFormValidationIntegration:
    def test_call_method_no_validation(self, client, settings):
        from dk_unicorn.components.unicorn_view import constructed_views_cache
        constructed_views_cache.clear()

        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.test_validation.FakeValidationComponent",
            action_queue=[
                {"type": "callMethod", "payload": {"name": "set_text_no_validation"}},
            ],
        )
        assert not response["errors"]

    def test_call_method_with_validation(self, client, settings):
        from dk_unicorn.components.unicorn_view import constructed_views_cache
        constructed_views_cache.clear()

        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.test_validation.FakeValidationComponent",
            action_queue=[
                {"type": "callMethod", "payload": {"name": "set_text_with_validation"}},
            ],
        )
        assert response["errors"]
        assert "number" in response["errors"]
        assert response["errors"]["number"][0]["code"] == "required"

    def test_call_method_validation_error_dict(self, client, settings):
        from dk_unicorn.components.unicorn_view import constructed_views_cache
        constructed_views_cache.clear()

        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.test_validation.FakeErrorComponent",
            action_queue=[
                {"type": "callMethod", "payload": {"name": "raise_dict_error"}},
            ],
        )
        assert response["errors"]
        assert "check" in response["errors"]
        assert response["errors"]["check"][0]["code"] == "required"

    def test_call_method_validation_error_string(self, client, settings):
        from dk_unicorn.components.unicorn_view import constructed_views_cache
        constructed_views_cache.clear()

        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.test_validation.FakeErrorComponent",
            action_queue=[
                {"type": "callMethod", "payload": {"name": "raise_string_error"}},
            ],
        )
        assert response["errors"]
        assert "__all__" in response["errors"]
        assert response["errors"]["__all__"][0]["code"] == "required"

    def test_call_method_validation_error_no_code(self, client, settings):
        from dk_unicorn.components.unicorn_view import constructed_views_cache
        constructed_views_cache.clear()

        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.test_validation.FakeErrorComponent",
            action_queue=[
                {"type": "callMethod", "payload": {"name": "raise_dict_error_no_code"}},
            ],
        )
        assert response["error"] == "Error code must be specified"

    def test_call_method_validation_error_list(self, client, settings):
        from dk_unicorn.components.unicorn_view import constructed_views_cache
        constructed_views_cache.clear()

        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.test_validation.FakeErrorComponent",
            action_queue=[
                {"type": "callMethod", "payload": {"name": "raise_list_error"}},
            ],
        )
        assert response["errors"]
        assert "__all__" in response["errors"]

    def test_call_method_validation_error_list_no_code(self, client, settings):
        from dk_unicorn.components.unicorn_view import constructed_views_cache
        constructed_views_cache.clear()

        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.test_validation.FakeErrorComponent",
            action_queue=[
                {"type": "callMethod", "payload": {"name": "raise_list_error_no_code"}},
            ],
        )
        assert response["error"] == "Error code must be specified"


class FakeValidationComponent(UnicornView):
    template_name = "templates/test_component.html"
    form_class = _ValidationForm
    text = "hello"
    number = ""

    def set_text_no_validation(self):
        self.text = "no validation"

    def set_text_with_validation(self):
        self.text = "validation 33"
        self.validate()


class FakeErrorComponent(UnicornView):
    template_name = "templates/test_component.html"
    check = False

    def raise_dict_error(self):
        raise ValidationError({"check": "Check is required"}, code="required")

    def raise_dict_error_no_code(self):
        raise ValidationError({"check": "Check is required"})

    def raise_string_error(self):
        raise ValidationError("Check is required", code="required")

    def raise_string_error_no_code(self):
        raise ValidationError("Check is required")

    def raise_list_error(self):
        raise ValidationError(
            [ValidationError({"check": "Check is required"})],
            code="required",
        )

    def raise_list_error_no_code(self):
        raise ValidationError(
            [ValidationError({"check": "Check is required"})],
        )
