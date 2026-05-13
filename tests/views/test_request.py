import time
from uuid import uuid4

import pytest
from django.test import RequestFactory

from dk_unicorn.utils import generate_checksum
from dk_unicorn.views.request import ComponentRequest


def _make_request(body, factory=None):
    if factory is None:
        factory = RequestFactory()
    import json
    req = factory.post("/unicorn/message/test", json.dumps(body), content_type="application/json")
    return req


def _valid_body(data=None, action_queue=None):
    if data is None:
        data = {}
    checksum = generate_checksum(data)
    return {
        "data": data,
        "id": str(uuid4()),
        "epoch": str(time.time()),
        "meta": f"{checksum}:somehash:{time.time()}",
        "actionQueue": action_queue or [],
    }


class TestComponentRequestParsing:
    def test_parses_data(self):
        body = _valid_body(data={"name": "World"})
        req = _make_request(body)
        cr = ComponentRequest(req, "test-component")
        assert cr.data == {"name": "World"}

    def test_parses_id(self):
        body = _valid_body()
        req = _make_request(body)
        cr = ComponentRequest(req, "test-component")
        assert cr.id == body["id"]

    def test_parses_epoch(self):
        body = _valid_body()
        req = _make_request(body)
        cr = ComponentRequest(req, "test-component")
        assert cr.epoch != ""

    def test_parses_hash_from_meta(self):
        body = _valid_body()
        req = _make_request(body)
        cr = ComponentRequest(req, "test-component")
        assert cr.hash == "somehash"

    def test_parses_name(self):
        body = _valid_body()
        req = _make_request(body)
        cr = ComponentRequest(req, "my-component")
        assert cr.name == "my-component"


class TestComponentRequestActions:
    def test_sync_input_action(self):
        body = _valid_body(action_queue=[
            {"type": "syncInput", "payload": {"name": "color", "value": "red"}},
        ])
        req = _make_request(body)
        cr = ComponentRequest(req, "test")
        assert len(cr.action_queue) == 1
        from dk_unicorn.views.action import SyncInput
        assert isinstance(cr.action_queue[0], SyncInput)
        assert cr.action_queue[0].name == "color"

    def test_call_method_action(self):
        body = _valid_body(action_queue=[
            {"type": "callMethod", "payload": {"name": "do_it"}},
        ])
        req = _make_request(body)
        cr = ComponentRequest(req, "test")
        from dk_unicorn.views.action import CallMethod
        assert isinstance(cr.action_queue[0], CallMethod)
        assert cr.action_queue[0].method_name == "do_it"

    def test_refresh_action(self):
        body = _valid_body(action_queue=[
            {"type": "callMethod", "payload": {"name": "$refresh"}},
        ])
        req = _make_request(body)
        cr = ComponentRequest(req, "test")
        from dk_unicorn.views.action import Refresh
        assert isinstance(cr.action_queue[0], Refresh)

    def test_reset_action(self):
        body = _valid_body(action_queue=[
            {"type": "callMethod", "payload": {"name": "$reset"}},
        ])
        req = _make_request(body)
        cr = ComponentRequest(req, "test")
        from dk_unicorn.views.action import Reset
        assert isinstance(cr.action_queue[0], Reset)

    def test_toggle_action(self):
        body = _valid_body(action_queue=[
            {"type": "callMethod", "payload": {"name": "$toggle('active')"}},
        ])
        req = _make_request(body)
        cr = ComponentRequest(req, "test")
        from dk_unicorn.views.action import Toggle
        assert isinstance(cr.action_queue[0], Toggle)

    def test_multiple_actions(self):
        body = _valid_body(action_queue=[
            {"type": "syncInput", "payload": {"name": "a", "value": "1"}},
            {"type": "callMethod", "payload": {"name": "save"}},
        ])
        req = _make_request(body)
        cr = ComponentRequest(req, "test")
        assert len(cr.action_queue) == 2


class TestComponentRequestChecksum:
    def test_valid_checksum_passes(self):
        body = _valid_body(data={"x": 1})
        req = _make_request(body)
        cr = ComponentRequest(req, "test")
        assert cr.data == {"x": 1}

    def test_invalid_checksum_raises(self):
        data = {"x": 1}
        body = {
            "data": data,
            "id": str(uuid4()),
            "epoch": str(time.time()),
            "meta": f"wrongchecksum:hash:{time.time()}",
            "actionQueue": [],
        }
        req = _make_request(body)
        with pytest.raises(AssertionError, match="Checksum does not match"):
            ComponentRequest(req, "test")
