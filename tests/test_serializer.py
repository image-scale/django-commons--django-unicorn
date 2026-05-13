import pytest

from dk_unicorn import serializer


def test_dumps_int():
    expected = '{"name":123}'
    actual = serializer.dumps({"name": 123})
    assert expected == actual


def test_dumps_string():
    expected = '{"name":"hello"}'
    actual = serializer.dumps({"name": "hello"})
    assert expected == actual


def test_dumps_float_converted_to_string():
    result = serializer.dumps({"price": 3.14})
    assert '"3.14"' in result


def test_dumps_nested_dict():
    data = {"outer": {"inner": "value"}}
    result = serializer.dumps(data)
    assert '"inner"' in result
    assert '"value"' in result


def test_dumps_list():
    data = {"items": [1, 2, 3]}
    result = serializer.dumps(data)
    assert "[1,2,3]" in result


def test_dumps_none():
    data = {"value": None}
    result = serializer.dumps(data)
    assert "null" in result


def test_dumps_bool():
    data = {"flag": True}
    result = serializer.dumps(data)
    assert "true" in result


def test_dumps_decimal():
    from decimal import Decimal
    data = {"amount": Decimal("19.99")}
    result = serializer.dumps(data)
    assert '"19.99"' in result


def test_dumps_sorted_keys():
    data = {"zebra": 1, "apple": 2}
    result = serializer.dumps(data)
    assert result.index("apple") < result.index("zebra")


def test_dumps_object_with_to_json():
    class CustomObj:
        def to_json(self):
            return {"custom": "data"}

    data = {"obj": CustomObj()}
    result = serializer.dumps(data)
    assert '"custom"' in result
    assert '"data"' in result


def test_dumps_no_fix_floats():
    data = {"price": 3.14}
    result = serializer.dumps(data, fix_floats=False)
    assert "3.14" in result
    assert '"3.14"' not in result


def test_dumps_empty_dict():
    result = serializer.dumps({})
    assert result == "{}"


def test_loads_valid_json():
    result = serializer.loads('{"name": "test"}')
    assert result == {"name": "test"}


def test_loads_invalid_json():
    with pytest.raises(serializer.JSONDecodeError):
        serializer.loads("not valid json{{{")


def test_loads_array():
    result = serializer.loads('[1, 2, 3]')
    assert result == [1, 2, 3]


def test_dumps_nested_float():
    data = {"outer": {"inner": 2.5}}
    result = serializer.dumps(data)
    parsed = serializer.loads(result)
    assert parsed["outer"]["inner"] == "2.5"


def test_dumps_float_in_list():
    data = {"items": [1.5, 2.5]}
    result = serializer.dumps(data)
    parsed = serializer.loads(result)
    assert parsed["items"] == ["1.5", "2.5"]


def test_invalid_field_name_error():
    err = serializer.InvalidFieldNameError(field_name="bad_field", data={"good": 1})
    assert err.field_name == "bad_field"
    assert err.data == {"good": 1}


def test_invalid_field_attribute_error():
    err = serializer.InvalidFieldAttributeError(
        field_name="field",
        field_attr="attr",
        data={"field": {"other": 1}},
    )
    assert err.field_name == "field"
    assert err.field_attr == "attr"
