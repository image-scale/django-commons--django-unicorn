from tests.views.utils import post_and_get_response
from dk_unicorn.signals import component_method_called


class TestMethodCalledSignalOnError:
    def test_method_called_signal_on_validation_error(self, client):
        received = []

        def handler(sender, **kwargs):
            received.append(kwargs)

        component_method_called.connect(handler)

        try:
            response = post_and_get_response(
                client,
                url="/unicorn/message/tests.views.fake_components.FakeComponent",
                data={"method_count": 0},
                action_queue=[
                    {"type": "callMethod", "payload": {"name": "test_method"}},
                ],
            )
            assert response["data"]["method_count"] == 1
            assert len(received) == 1
            assert received[0]["success"] is True
            assert received[0]["error"] is None
        finally:
            component_method_called.disconnect(handler)
