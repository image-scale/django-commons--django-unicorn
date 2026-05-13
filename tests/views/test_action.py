import pytest

from dk_unicorn.views.action import Action, CallMethod, Refresh, Reset, SyncInput, Toggle


class TestAction:
    def test_action_type(self):
        a = Action({"type": "syncInput", "payload": {"name": "x"}})
        assert a.action_type == "syncInput"

    def test_action_payload(self):
        a = Action({"type": "callMethod", "payload": {"name": "do_it"}})
        assert a.payload == {"name": "do_it"}

    def test_action_partials_default(self):
        a = Action({"type": "syncInput", "payload": {}})
        assert a.partials == []

    def test_action_partials_from_list(self):
        a = Action({"type": "syncInput", "payload": {}, "partials": [{"key": "p1"}]})
        assert a.partials == [{"key": "p1"}]

    def test_action_partial_legacy(self):
        a = Action({"type": "syncInput", "payload": {}, "partial": {"key": "leg"}})
        assert {"key": "leg"} in a.partials


class TestSyncInput:
    def test_name_and_value(self):
        si = SyncInput({"type": "syncInput", "payload": {"name": "color", "value": "blue"}})
        assert si.name == "color"
        assert si.value == "blue"
        assert si.action_type == "syncInput"

    def test_defaults(self):
        si = SyncInput({"type": "syncInput", "payload": {}})
        assert si.name == ""
        assert si.value == ""


class TestCallMethod:
    def test_simple_method(self):
        cm = CallMethod({"type": "callMethod", "payload": {"name": "do_something"}})
        assert cm.method_name == "do_something"
        assert cm.args == ()
        assert cm.kwargs == {}

    def test_method_with_args(self):
        cm = CallMethod({"type": "callMethod", "payload": {"name": "add(1, 2)"}})
        assert cm.method_name == "add"
        assert cm.args == (1, 2)

    def test_method_with_kwargs(self):
        cm = CallMethod({"type": "callMethod", "payload": {"name": "set(count=5)"}})
        assert cm.method_name == "set"
        assert cm.kwargs == {"count": 5}


class TestSpecialActions:
    def test_reset(self):
        r = Reset({"type": "callMethod", "payload": {"name": "$reset"}})
        assert isinstance(r, Action)

    def test_refresh(self):
        r = Refresh({"type": "callMethod", "payload": {"name": "$refresh"}})
        assert isinstance(r, Action)

    def test_toggle(self):
        t = Toggle({"type": "callMethod", "payload": {"name": "$toggle('check')"}})
        assert isinstance(t, Action)
        assert t.method_name == "$toggle"
        assert t.args == ("check",)
