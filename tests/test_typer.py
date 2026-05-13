import pytest
from datetime import datetime, date, time, timedelta
from uuid import UUID

from dk_unicorn.typer import cast_value, cast_attribute_value, get_type_hints


def test_cast_value_int():
    assert cast_value(int, "42") == 42


def test_cast_value_int_already_int():
    assert cast_value(int, 42) == 42


def test_cast_value_float():
    assert cast_value(float, "3.14") == 3.14


def test_cast_value_bool_true():
    assert cast_value(bool, "True") is True


def test_cast_value_bool_false():
    assert cast_value(bool, "False") is False


def test_cast_value_bool_other():
    assert cast_value(bool, "yes") is False


def test_cast_value_datetime():
    result = cast_value(datetime, "2020-09-12T01:02:03")
    assert isinstance(result, datetime)
    assert result.year == 2020
    assert result.month == 9
    assert result.day == 12
    assert result.hour == 1
    assert result.minute == 2
    assert result.second == 3


def test_cast_value_date():
    result = cast_value(date, "2020-09-12")
    assert isinstance(result, date)
    assert result.year == 2020
    assert result.month == 9
    assert result.day == 12


def test_cast_value_time():
    result = cast_value(time, "01:02:03")
    assert isinstance(result, time)
    assert result.hour == 1
    assert result.minute == 2
    assert result.second == 3


def test_cast_value_timedelta():
    result = cast_value(timedelta, "1 00:00:00")
    assert isinstance(result, timedelta)
    assert result.days == 1


def test_cast_value_uuid():
    uuid_str = "12345678-1234-5678-1234-567812345678"
    result = cast_value(UUID, uuid_str)
    assert isinstance(result, UUID)
    assert str(result) == uuid_str


def test_cast_value_optional_none():
    from typing import Optional
    result = cast_value(Optional[int], None)
    assert result is None


def test_cast_value_optional_with_value():
    from typing import Optional
    result = cast_value(Optional[int], "42")
    assert result == 42


def test_cast_value_union():
    from typing import Union
    result = cast_value(Union[int, str], "42")
    assert result == 42


def test_cast_value_list_int():
    result = cast_value(list[int], ["1", "2", "3"])
    assert result == [1, 2, 3]


def test_cast_value_list_no_args():
    result = cast_value(list, [1, 2, 3])
    assert result == [1, 2, 3]


def test_cast_value_dict():
    result = cast_value(dict[str, int], {"a": "1", "b": "2"})
    assert result == {"a": 1, "b": 2}


def test_cast_value_str():
    result = cast_value(str, 42)
    assert result == "42"


def test_cast_value_datetime_from_epoch():
    epoch = 1600000000
    result = cast_value(datetime, epoch)
    assert isinstance(result, datetime)


def test_cast_value_date_from_epoch():
    epoch = 1600000000
    result = cast_value(date, epoch)
    assert isinstance(result, date)


def test_cast_attribute_value():
    class TestObj:
        count: int = 0

    obj = TestObj()
    result = cast_attribute_value(obj, "count", "42")
    assert result == 42


def test_cast_attribute_value_no_hint():
    class TestObj:
        name = "hello"

    obj = TestObj()
    result = cast_attribute_value(obj, "name", "world")
    assert result == "world"


def test_cast_attribute_value_bool():
    class TestObj:
        flag: bool = False

    obj = TestObj()
    result = cast_attribute_value(obj, "flag", "True")
    assert result is True


def test_get_type_hints_class():
    class MyClass:
        name: str = ""
        count: int = 0

    hints = get_type_hints(MyClass)
    assert hints["name"] is str
    assert hints["count"] is int


def test_get_type_hints_instance():
    class MyClass:
        name: str = ""

    obj = MyClass()
    hints = get_type_hints(obj)
    assert hints["name"] is str


def test_get_type_hints_inheritance():
    class Parent:
        name: str = ""

    class Child(Parent):
        age: int = 0

    hints = get_type_hints(Child)
    assert "name" in hints
    assert "age" in hints


def test_cast_value_dataclass():
    import dataclasses

    @dataclasses.dataclass
    class Point:
        x: int
        y: int

    result = cast_value(Point, {"x": 1, "y": 2})
    assert result.x == 1
    assert result.y == 2


def test_cast_value_tuple_homogeneous():
    result = cast_value(tuple[int], ["1", "2"])
    assert result == (1, 2)


def test_cast_value_invalid_returns_original():
    result = cast_value(int, "not_a_number")
    assert result == "not_a_number"
