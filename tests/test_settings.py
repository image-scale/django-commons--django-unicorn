from dk_unicorn.settings import (
    get_settings,
    get_setting,
    get_cache_alias,
    get_serial_enabled,
    get_serial_timeout,
    get_minify_html_enabled,
    get_script_location,
)


def test_get_settings(settings):
    settings.UNICORN = {"APPS": ("test_app",)}
    result = get_settings()
    assert result == {"APPS": ("test_app",)}


def test_get_settings_legacy(settings):
    settings.DJANGO_UNICORN = {"APPS": ("legacy_app",)}
    result = get_settings()
    assert result == {"APPS": ("legacy_app",)}


def test_get_setting(settings):
    settings.UNICORN = {"CACHE_ALIAS": "custom_cache"}
    result = get_setting("CACHE_ALIAS")
    assert result == "custom_cache"


def test_get_setting_default(settings):
    settings.UNICORN = {}
    result = get_setting("NONEXISTENT", "fallback")
    assert result == "fallback"


def test_get_cache_alias_default(settings):
    settings.UNICORN = {}
    result = get_cache_alias()
    assert result == "default"


def test_get_cache_alias_custom(settings):
    settings.UNICORN = {"CACHE_ALIAS": "redis"}
    result = get_cache_alias()
    assert result == "redis"


def test_get_serial_enabled_false(settings):
    settings.UNICORN = {"SERIAL": {"ENABLED": False}}
    assert get_serial_enabled() is False


def test_get_serial_enabled_true(settings):
    settings.UNICORN = {"SERIAL": {"ENABLED": True}}
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
    assert get_serial_enabled() is True


def test_get_serial_enabled_dummy_cache(settings):
    settings.UNICORN = {"SERIAL": {"ENABLED": True}}
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }
    assert get_serial_enabled() is False


def test_get_serial_timeout(settings):
    settings.UNICORN = {"SERIAL": {"TIMEOUT": 30}}
    assert get_serial_timeout() == 30


def test_get_serial_timeout_default(settings):
    settings.UNICORN = {"SERIAL": {}}
    assert get_serial_timeout() == 60


def test_get_minify_html_enabled_false(settings):
    settings.UNICORN = {"MINIFY_HTML": False}
    assert get_minify_html_enabled() is False


def test_get_script_location_default(settings):
    settings.UNICORN = {}
    assert get_script_location() == "after"


def test_get_script_location_custom(settings):
    settings.UNICORN = {"SCRIPT_LOCATION": "append"}
    assert get_script_location() == "append"
