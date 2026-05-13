import logging

from dk_unicorn.decorators import timed


def test_timed_passes_through_in_production(settings):
    settings.DEBUG = False

    @timed
    def add(a, b):
        return a + b

    assert add(2, 3) == 5


def test_timed_returns_result_in_debug(settings):
    settings.DEBUG = True

    @timed
    def multiply(a, b):
        return a * b

    assert multiply(4, 5) == 20


def test_timed_logs_in_debug(settings, caplog):
    settings.DEBUG = True

    @timed
    def greet(name):
        return f"Hello, {name}"

    with caplog.at_level(logging.DEBUG, logger="profile"):
        result = greet("Alice")

    assert result == "Hello, Alice"
    assert "greet(" in caplog.text
    assert "ms" in caplog.text


def test_timed_no_log_in_production(settings, caplog):
    settings.DEBUG = False

    @timed
    def greet(name):
        return f"Hello, {name}"

    with caplog.at_level(logging.DEBUG, logger="profile"):
        result = greet("World")

    assert result == "Hello, World"
    assert "greet(" not in caplog.text


def test_timed_preserves_function_name():
    @timed
    def my_function():
        pass

    assert my_function.__name__ == "my_function"


def test_timed_with_kwargs(settings, caplog):
    settings.DEBUG = True

    @timed
    def func(a, b=10):
        return a + b

    with caplog.at_level(logging.DEBUG, logger="profile"):
        result = func(1, b=20)

    assert result == 21
    assert "func(" in caplog.text
    assert "b=" in caplog.text


def test_timed_string_kwarg_quoted(settings, caplog):
    settings.DEBUG = True

    @timed
    def func(name="default"):
        return name

    with caplog.at_level(logging.DEBUG, logger="profile"):
        result = func(name="test")

    assert result == "test"
    assert "name='test'" in caplog.text


def test_timed_no_args(settings, caplog):
    settings.DEBUG = True

    @timed
    def func():
        return 42

    with caplog.at_level(logging.DEBUG, logger="profile"):
        result = func()

    assert result == 42
    assert "func(): " in caplog.text
