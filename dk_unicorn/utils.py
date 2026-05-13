import hmac
import inspect
from collections.abc import Sequence, Set

import shortuuid
from django.conf import settings as django_settings
from django.template import Template, engines
from django.utils.safestring import SafeText, mark_safe


_JSON_ESCAPE_TABLE = str.maketrans({
    "&": "\\u0026",
    "<": "\\u003C",
    ">": "\\u003E",
})


def generate_checksum(data):
    if isinstance(data, dict):
        data = str(data)
    if isinstance(data, str):
        data = data.encode("utf-8")
    if not isinstance(data, bytes):
        raise TypeError(f"Cannot generate checksum for type {type(data)}")

    secret = django_settings.SECRET_KEY
    if isinstance(secret, str):
        secret = secret.encode("utf-8")

    checksum = hmac.new(secret, data, digestmod="sha256").hexdigest()
    return shortuuid.uuid(checksum)[:8]


def get_method_arguments(func):
    sig = inspect.signature(func)
    return list(sig.parameters.keys())


def sanitize_html(html_str):
    return mark_safe(html_str.translate(_JSON_ESCAPE_TABLE))


def is_non_string_sequence(obj):
    if isinstance(obj, (str, bytes, bytearray)):
        return False
    return isinstance(obj, (Sequence, Set))


def is_int(s):
    try:
        int(s)
        return True
    except (ValueError, TypeError):
        return False


def create_template(template_html, engine_name=None):
    if callable(template_html):
        template_html = template_html()

    all_engines = engines.all() if engine_name is None else [engines[engine_name]]

    for engine in all_engines:
        try:
            return engine.from_string(template_html)
        except Exception:
            continue

    raise AssertionError("No template engine could process the template HTML")
