import time
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from dk_unicorn.errors import UnicornAuthenticationError
from dk_unicorn.views import _check_auth, _handle_serial_queue
from dk_unicorn.views.request import ComponentRequest
from tests.views.utils import post_and_get_response


class TestAuthEnforcement:
    def test_no_middleware_no_check(self, settings, rf):
        settings.MIDDLEWARE = []
        component = MagicMock()
        request = rf.get("/")
        _check_auth(request, component)

    def test_middleware_authenticated_user(self, settings, rf):
        settings.MIDDLEWARE = ["django.contrib.auth.middleware.LoginRequiredMiddleware"]
        component = MagicMock(spec=[])
        request = rf.get("/")
        request.user = MagicMock(is_authenticated=True)
        _check_auth(request, component)

    def test_middleware_unauthenticated_user_raises(self, settings, rf):
        settings.MIDDLEWARE = ["django.contrib.auth.middleware.LoginRequiredMiddleware"]
        component = MagicMock(spec=[])
        request = rf.get("/")
        request.user = MagicMock(is_authenticated=False)
        with pytest.raises(UnicornAuthenticationError, match="Authentication required"):
            _check_auth(request, component)

    def test_middleware_unauthenticated_login_not_required(self, settings, rf):
        settings.MIDDLEWARE = ["django.contrib.auth.middleware.LoginRequiredMiddleware"]

        class Meta:
            login_not_required = True

        component = MagicMock()
        component.Meta = Meta
        request = rf.get("/")
        request.user = MagicMock(is_authenticated=False)
        _check_auth(request, component)

    def test_middleware_no_user(self, settings, rf):
        settings.MIDDLEWARE = ["django.contrib.auth.middleware.LoginRequiredMiddleware"]
        component = MagicMock(spec=[])
        request = rf.get("/")
        if hasattr(request, "user"):
            del request.user
        _check_auth(request, component)


class TestSerialQueue:
    def test_serial_disabled_processes_directly(self, settings, client):
        settings.UNICORN = {**settings.UNICORN, "SERIAL": {"ENABLED": False}}
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            data={"method_count": 0},
            action_queue=[
                {"type": "callMethod", "payload": {"name": "test_method"}},
            ],
        )
        assert response["data"]["method_count"] == 1

    def test_serial_enabled_processes_request(self, settings, client):
        settings.UNICORN = {**settings.UNICORN, "SERIAL": {"ENABLED": True, "TIMEOUT": 5}}
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            data={"method_count": 0},
            action_queue=[
                {"type": "callMethod", "payload": {"name": "test_method"}},
            ],
        )
        assert response["data"]["method_count"] == 1

    def test_ignore_m2m_in_initial_data(self, settings, client):
        response = post_and_get_response(
            client,
            url="/unicorn/message/tests.views.fake_components.FakeComponent",
            data={"method_count": 0},
            action_queue=[
                {"type": "callMethod", "payload": {"name": "test_method"}},
            ],
        )
        assert response["data"]["method_count"] == 1
