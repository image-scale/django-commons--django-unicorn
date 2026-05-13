import pytest
from django.http import HttpResponseRedirect

from dk_unicorn.components.updaters import HashUpdate, LocationUpdate, PollUpdate
from dk_unicorn.views.objects import Return


def test_return_basic():
    r = Return("test_method")
    assert r.method_name == "test_method"
    assert r.args == []
    assert r.kwargs == {}
    assert r.value == {}
    assert r.redirect == {}
    assert r.poll == {}


def test_return_with_args_kwargs():
    r = Return("my_method", args=[1, 2], kwargs={"key": "val"})
    assert r.args == [1, 2]
    assert r.kwargs == {"key": "val"}


def test_return_value_simple():
    r = Return("method")
    r.value = "hello"
    assert r.value == "hello"


def test_return_value_none():
    r = Return("method")
    r.value = None
    assert r.value is None
    assert r.redirect == {}


def test_return_get_data():
    r = Return("add", args=[1, 2], kwargs={"extra": 3})
    r.value = 42
    data = r.get_data()
    assert data["method"] == "add"
    assert data["args"] == [1, 2]
    assert data["kwargs"] == {"extra": 3}
    assert data["value"] == 42


def test_return_redirect():
    r = Return("go")
    r.value = HttpResponseRedirect("/new-page/")
    assert r.redirect == {"url": "/new-page/"}
    assert r.value == {"url": "/new-page/"}


def test_return_redirect_get_data():
    r = Return("go")
    r.value = HttpResponseRedirect("/page/")
    data = r.get_data()
    assert data["value"] == {"url": "/page/"}


def test_return_hash_update():
    r = Return("update_hash")
    r.value = HashUpdate("#section-2")
    assert r.redirect == {"hash": "#section-2"}
    assert r.value == {"hash": "#section-2"}


def test_return_location_update():
    redirect_response = HttpResponseRedirect("/other/")
    r = Return("navigate")
    r.value = LocationUpdate(redirect_response, title="Other Page")
    assert r.redirect["url"] == "/other/"
    assert r.redirect["refresh"] is True
    assert r.redirect["title"] == "Other Page"


def test_return_poll_update():
    r = Return("poll")
    r.value = PollUpdate(timing=5000, method="check_status", disable=False)
    assert r.poll == {"timing": 5000, "method": "check_status", "disable": False}


def test_return_poll_update_disable():
    r = Return("stop_poll")
    r.value = PollUpdate(disable=True)
    assert r.poll["disable"] is True


def test_return_get_data_empty():
    r = Return("m")
    data = r.get_data()
    assert data["method"] == "m"
    assert data["value"] == {}
    assert data["args"] == []
    assert data["kwargs"] == {}


def test_return_get_data_with_dict_value():
    r = Return("info")
    r.value = {"name": "Alice", "age": 30}
    data = r.get_data()
    assert data["value"]["name"] == "Alice"
    assert data["value"]["age"] == 30


def test_return_get_data_with_list_value():
    r = Return("items")
    r.value = [1, 2, 3]
    data = r.get_data()
    assert data["value"] == [1, 2, 3]
