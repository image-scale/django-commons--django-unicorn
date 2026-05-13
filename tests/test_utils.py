import pytest

from dk_unicorn.utils import (
    generate_checksum,
    get_method_arguments,
    sanitize_html,
    is_non_string_sequence,
    is_int,
    create_template,
)


def test_generate_checksum_bytes(settings):
    settings.SECRET_KEY = "asdf"
    expected = "TfxFqcQL"
    actual = generate_checksum(b'{"name": "test"}')
    assert expected == actual


def test_generate_checksum_str(settings):
    settings.SECRET_KEY = "asdf"
    result = generate_checksum('{"name": "test"}')
    assert isinstance(result, str)
    assert len(result) == 8


def test_generate_checksum_dict(settings):
    settings.SECRET_KEY = "asdf"
    result = generate_checksum({"name": "test"})
    assert isinstance(result, str)
    assert len(result) == 8


def test_generate_checksum_invalid_type():
    with pytest.raises(TypeError):
        generate_checksum(123)


def test_generate_checksum_consistency(settings):
    settings.SECRET_KEY = "test-key"
    c1 = generate_checksum(b"hello")
    c2 = generate_checksum(b"hello")
    assert c1 == c2


def test_generate_checksum_different_for_different_data(settings):
    settings.SECRET_KEY = "test-key"
    c1 = generate_checksum(b"hello")
    c2 = generate_checksum(b"world")
    assert c1 != c2


def test_get_method_arguments():
    def example_func(a, b, c=5):
        pass

    result = get_method_arguments(example_func)
    assert result == ["a", "b", "c"]


def test_get_method_arguments_no_args():
    def no_args():
        pass

    result = get_method_arguments(no_args)
    assert result == []


def test_get_method_arguments_self():
    class MyClass:
        def method(self, x, y):
            pass

    result = get_method_arguments(MyClass.method)
    assert result == ["self", "x", "y"]


def test_sanitize_html_escapes_ampersand():
    result = sanitize_html("a & b")
    assert "\\u0026" in result
    assert "&" not in str(result).replace("\\u0026", "")


def test_sanitize_html_escapes_lt_gt():
    result = sanitize_html("<script>alert('xss')</script>")
    assert "\\u003C" in result
    assert "\\u003E" in result


def test_sanitize_html_plain_text():
    result = sanitize_html("hello world")
    assert str(result) == "hello world"


def test_is_non_string_sequence_list():
    assert is_non_string_sequence([1, 2, 3]) is True


def test_is_non_string_sequence_tuple():
    assert is_non_string_sequence((1, 2, 3)) is True


def test_is_non_string_sequence_set():
    assert is_non_string_sequence({1, 2, 3}) is True


def test_is_non_string_sequence_string():
    assert is_non_string_sequence("hello") is False


def test_is_non_string_sequence_bytes():
    assert is_non_string_sequence(b"hello") is False


def test_is_non_string_sequence_int():
    assert is_non_string_sequence(42) is False


def test_is_non_string_sequence_dict():
    assert is_non_string_sequence({"a": 1}) is False


def test_is_int_valid():
    assert is_int("42") is True


def test_is_int_invalid():
    assert is_int("abc") is False


def test_is_int_negative():
    assert is_int("-5") is True


def test_is_int_float_string():
    assert is_int("3.14") is False


def test_create_template():
    tpl = create_template("<div>{{ name }}</div>")
    assert tpl is not None


def test_create_template_callable():
    tpl = create_template(lambda: "<div>{{ name }}</div>")
    assert tpl is not None
