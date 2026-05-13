from django.conf import settings as django_settings

SETTINGS_KEY = "UNICORN"
LEGACY_SETTINGS_KEY = "DJANGO_UNICORN"


def get_settings():
    if hasattr(django_settings, LEGACY_SETTINGS_KEY):
        return getattr(django_settings, LEGACY_SETTINGS_KEY)
    if hasattr(django_settings, SETTINGS_KEY):
        return getattr(django_settings, SETTINGS_KEY)
    return {}


def get_setting(key, default=None):
    return get_settings().get(key, default)


def get_cache_alias():
    return get_setting("CACHE_ALIAS", "default")


def get_serial_settings():
    return get_setting("SERIAL", {})


def get_serial_enabled():
    enabled = get_serial_settings().get("ENABLED", False)
    if enabled:
        cache_alias = get_cache_alias()
        from django.core.cache import caches
        cache_backend = caches[cache_alias]
        backend_path = django_settings.CACHES.get(cache_alias, {}).get("BACKEND", "")
        if "DummyCache" in backend_path:
            return False
    return enabled


def get_serial_timeout():
    return get_serial_settings().get("TIMEOUT", 60)


def get_minify_html_enabled():
    enabled = get_setting("MINIFY_HTML", False)
    if enabled:
        try:
            import htmlmin  # noqa: F401
        except ImportError:
            return False
    return enabled


def get_script_location():
    return get_setting("SCRIPT_LOCATION", "after")
