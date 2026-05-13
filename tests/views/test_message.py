import time
from uuid import uuid4

import pytest
from django.test import RequestFactory

from dk_unicorn.views import message
from tests.views.utils import post_and_get_response


def _post_json(client, data, url="/unicorn/message/test-message"):
    return client.post(url, data, content_type="application/json")


class TestMessageViewHTTP:
    def test_requires_post(self, client):
        response = client.get("/unicorn/message/test-component")
        assert response.status_code == 405

    def test_csrf_required(self, rf):
        request = rf.post("/unicorn/message/test-csrf")
        response = message(request, component_name="test-csrf")
        assert response.status_code == 403

    def test_missing_component_name(self, client):
        response = client.post("/unicorn/message/", content_type="application/json")
        assert response.status_code == 404


class TestMessageViewValidation:
    def test_no_body(self, client):
        response = _post_json(client, b"not-json", url="/unicorn/message/test-no-body")
        body = response.json()
        assert "error" in body

    def test_bad_checksum(self, client):
        data = {
            "data": {},
            "meta": "badchecksum",
            "id": str(uuid4()),
            "epoch": time.time(),
        }
        response = _post_json(client, data, url="/unicorn/message/test-bad-checksum")
        body = response.json()
        assert body.get("error") == "Checksum does not match"


class TestMessageViewSyncInput:
    def test_sync_input(self, client):
        data = {"method_count": 0}
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            data=data,
            action_queue=[
                {"type": "syncInput", "payload": {"name": "method_count", "value": 5}},
            ],
        )
        assert response["data"]["method_count"] == 5

    def test_sync_input_nested(self, client):
        data = {"dictionary": {"name": "test"}}
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            data=data,
            action_queue=[
                {"type": "syncInput", "payload": {"name": "dictionary.name", "value": "updated"}},
            ],
        )
        assert response["data"]["dictionary"]["name"] == "updated"


class TestMessageViewCallMethod:
    def test_call_method(self, client):
        data = {"method_count": 0}
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            data=data,
            action_queue=[
                {"type": "callMethod", "payload": {"name": "test_method"}},
            ],
        )
        assert response["data"]["method_count"] == 1

    def test_call_method_with_args(self, client):
        data = {"method_count": 0}
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            data=data,
            action_queue=[
                {"type": "callMethod", "payload": {"name": "test_method_args(7)"}},
            ],
        )
        assert response["data"]["method_count"] == 7

    def test_call_method_with_kwargs(self, client):
        data = {"method_count": 0}
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            data=data,
            action_queue=[
                {"type": "callMethod", "payload": {"name": "test_method_kwargs(count=99)"}},
            ],
        )
        assert response["data"]["method_count"] == 99

    def test_call_method_return_value(self, client):
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            action_queue=[
                {"type": "callMethod", "payload": {"name": "test_return_value"}},
            ],
        )
        assert "return" in response
        assert response["return"]["value"] == "booya"

    def test_call_method_redirect(self, client):
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            action_queue=[
                {"type": "callMethod", "payload": {"name": "redirect_action"}},
            ],
        )
        assert "redirect" in response
        assert response["redirect"]["url"] == "/new-page/"

    def test_call_method_hash_update(self, client):
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            action_queue=[
                {"type": "callMethod", "payload": {"name": "hash_action"}},
            ],
        )
        assert "redirect" in response
        assert response["redirect"]["hash"] == "#section-2"

    def test_call_method_poll_update(self, client):
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            action_queue=[
                {"type": "callMethod", "payload": {"name": "poll_action"}},
            ],
        )
        assert "poll" in response
        assert response["poll"]["timing"] == 3000
        assert response["poll"]["method"] == "check_status"

    def test_setter_method(self, client):
        data = {"method_count": 0}
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            data=data,
            action_queue=[
                {"type": "callMethod", "payload": {"name": "method_count=42"}},
            ],
        )
        assert response["data"]["method_count"] == 42

    def test_validate_action(self, client):
        data = {"method_count": 0}
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            data=data,
            action_queue=[
                {"type": "callMethod", "payload": {"name": "$validate"}},
            ],
        )
        assert "data" in response


class TestMessageViewReset:
    def test_reset(self, client):
        data = {"method_count": 42}
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            data=data,
            action_queue=[
                {"type": "callMethod", "payload": {"name": "$reset"}},
            ],
        )
        assert response["data"]["method_count"] == 0


class TestMessageViewToggle:
    def test_toggle_false_to_true(self, client):
        data = {"check": False}
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            data=data,
            action_queue=[
                {"type": "callMethod", "payload": {"name": "$toggle('check')"}},
            ],
        )
        assert response["data"]["check"] is True

    def test_toggle_true_to_false(self, client):
        data = {"check": True}
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            data=data,
            action_queue=[
                {"type": "callMethod", "payload": {"name": "$toggle('check')"}},
            ],
        )
        assert response["data"]["check"] is False


class TestMessageViewResponse:
    def test_response_has_id(self, client):
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            action_queue=[
                {"type": "callMethod", "payload": {"name": "test_method"}},
            ],
        )
        assert "id" in response

    def test_response_has_dom(self, client):
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            action_queue=[
                {"type": "callMethod", "payload": {"name": "test_method"}},
            ],
        )
        assert "dom" in response

    def test_response_has_data(self, client):
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            action_queue=[
                {"type": "callMethod", "payload": {"name": "test_method"}},
            ],
        )
        assert "data" in response

    def test_response_has_errors(self, client):
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            action_queue=[
                {"type": "callMethod", "payload": {"name": "test_method"}},
            ],
        )
        assert "errors" in response

    def test_response_has_calls(self, client):
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            action_queue=[
                {"type": "callMethod", "payload": {"name": "test_method"}},
            ],
        )
        assert "calls" in response
