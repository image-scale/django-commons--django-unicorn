from types import MappingProxyType

from dk_unicorn.call_method_parser import (
    parse_call_method_name,
    parse_kwarg,
    eval_value,
    InvalidKwargError,
)


def setup_function():
    parse_call_method_name.cache_clear()
    parse_kwarg.cache_clear()
    eval_value.cache_clear()


def test_parse_method_no_args():
    name, args, kwargs = parse_call_method_name("do_something()")
    assert name == "do_something"
    assert args == ()
    assert kwargs == MappingProxyType({})


def test_parse_method_string_arg():
    name, args, kwargs = parse_call_method_name("set_name('Bob')")
    assert name == "set_name"
    assert args == ("Bob",)
    assert kwargs == MappingProxyType({})


def test_parse_method_int_arg():
    name, args, kwargs = parse_call_method_name("set_count(42)")
    assert name == "set_count"
    assert args == (42,)


def test_parse_method_multiple_args():
    name, args, kwargs = parse_call_method_name("update(1, 'hello', True)")
    assert name == "update"
    assert args == (1, "hello", True)


def test_parse_method_with_kwargs():
    name, args, kwargs = parse_call_method_name("set_val(1, key='test')")
    assert name == "set_val"
    assert args == (1,)
    assert kwargs == MappingProxyType({"key": "test"})


def test_parse_method_only_kwargs():
    name, args, kwargs = parse_call_method_name("configure(width=100, height=200)")
    assert name == "configure"
    assert args == ()
    assert kwargs["width"] == 100
    assert kwargs["height"] == 200


def test_parse_special_method():
    name, args, kwargs = parse_call_method_name("$refresh()")
    assert name == "$refresh"
    assert args == ()


def test_parse_special_method_no_parens():
    name, args, kwargs = parse_call_method_name("$reset")
    assert name == "$reset"
    assert args == ()


def test_parse_method_no_parens():
    name, args, kwargs = parse_call_method_name("simple_method")
    assert name == "simple_method"
    assert args == ()
    assert kwargs == MappingProxyType({})


def test_parse_method_dotted_name():
    name, args, kwargs = parse_call_method_name("obj.method()")
    assert name == "obj.method"
    assert args == ()


def test_parse_kwarg_string():
    result = parse_kwarg("test='1'")
    assert result == {"test": "1"}


def test_parse_kwarg_int():
    result = parse_kwarg("count=42")
    assert result == {"count": 42}


def test_parse_kwarg_bool():
    result = parse_kwarg("flag=True")
    assert result == {"flag": True}


def test_parse_kwarg_invalid():
    result = parse_kwarg("not valid kwarg")
    assert result == {}


def test_parse_kwarg_raise_if_unparseable():
    import pytest
    with pytest.raises(InvalidKwargError):
        parse_kwarg("not valid", raise_if_unparseable=True)


def test_eval_value_int():
    assert eval_value("42") == 42


def test_eval_value_float():
    assert eval_value("3.14") == 3.14


def test_eval_value_string():
    assert eval_value("'hello'") == "hello"


def test_eval_value_bool():
    assert eval_value("True") is True
    assert eval_value("False") is False


def test_eval_value_none():
    assert eval_value("None") is None


def test_eval_value_list():
    assert eval_value("[1, 2, 3]") == [1, 2, 3]


def test_eval_value_dict():
    assert eval_value("{'a': 1}") == {"a": 1}


def test_eval_value_datetime_string():
    result = eval_value("2020-09-12T01:02:03")
    from datetime import datetime
    assert isinstance(result, datetime)


def test_eval_value_uuid_string():
    result = eval_value("12345678-1234-5678-1234-567812345678")
    from uuid import UUID
    assert isinstance(result, UUID)


def test_parse_method_with_negative_int():
    name, args, kwargs = parse_call_method_name("adjust(-5)")
    assert name == "adjust"
    assert args == (-5,)


def test_kwargs_immutable():
    _, _, kwargs = parse_call_method_name("test(x=1)")
    assert isinstance(kwargs, MappingProxyType)
    import pytest
    with pytest.raises(TypeError):
        kwargs["y"] = 2
