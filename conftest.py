import pytest
from django.conf import settings


def pytest_configure():
    templates = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": ["tests"],
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.request",
                    "django.contrib.messages.context_processors.messages",
                ],
            },
        }
    ]

    databases = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
        }
    }

    installed_apps = [
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.contenttypes",
        "django.contrib.auth",
        "dk_unicorn",
        "example.coffee.apps.Config",
        "example.books.apps.Config",
    ]

    unicorn_settings = {
        "SERIAL": {"ENABLED": True, "TIMEOUT": 5},
        "CACHE_ALIAS": "default",
        "APPS": ("unicorn",),
        "MINIFY_HTML": False,
        "SCRIPT_LOCATION": "after",
    }

    caches = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        }
    }

    settings.configure(
        DEBUG=True,
        SECRET_KEY="this-is-a-secret",
        TEMPLATES=templates,
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ],
        ROOT_URLCONF="tests.urls",
        DATABASES=databases,
        INSTALLED_APPS=installed_apps,
        UNIT_TEST=True,
        UNICORN=unicorn_settings,
        CACHES=caches,
        MESSAGE_STORAGE="django.contrib.messages.storage.session.SessionStorage",
        SESSION_ENGINE="django.contrib.sessions.backends.file",
    )


@pytest.fixture(autouse=True)
def reset_settings(settings):
    cache_settings = {**settings.CACHES}
    unicorn_settings = {**settings.UNICORN}
    django_unicorn_settings = {}

    if hasattr(settings, "DJANGO_UNICORN"):
        django_unicorn_settings = {**settings.DJANGO_UNICORN}

    yield

    settings.CACHES = cache_settings
    settings.UNICORN = unicorn_settings

    if django_unicorn_settings:
        settings.DJANGO_UNICORN = django_unicorn_settings
