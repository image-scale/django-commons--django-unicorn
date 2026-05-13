from dk_unicorn.signals import (
    component_mounted,
    component_hydrated,
    component_completed,
    component_rendered,
    component_parent_rendered,
    component_property_updating,
    component_property_updated,
    component_property_resolved,
    component_method_calling,
    component_method_called,
    component_pre_parsed,
    component_post_parsed,
)


def test_all_signals_exist():
    signals = [
        component_mounted,
        component_hydrated,
        component_completed,
        component_rendered,
        component_parent_rendered,
        component_property_updating,
        component_property_updated,
        component_property_resolved,
        component_method_calling,
        component_method_called,
        component_pre_parsed,
        component_post_parsed,
    ]
    assert len(signals) == 12
    for sig in signals:
        assert sig is not None


def test_signal_send_and_receive():
    received = []

    def handler(sender, **kwargs):
        received.append({"sender": sender, "kwargs": kwargs})

    component_mounted.connect(handler)
    try:
        component_mounted.send(sender=str, component="test_component")
        assert len(received) == 1
        assert received[0]["sender"] == str
        assert received[0]["kwargs"]["component"] == "test_component"
    finally:
        component_mounted.disconnect(handler)


def test_signal_multiple_receivers():
    count = [0]

    def handler1(sender, **kwargs):
        count[0] += 1

    def handler2(sender, **kwargs):
        count[0] += 10

    component_hydrated.connect(handler1)
    component_hydrated.connect(handler2)
    try:
        component_hydrated.send(sender=str, component="test")
        assert count[0] == 11
    finally:
        component_hydrated.disconnect(handler1)
        component_hydrated.disconnect(handler2)
