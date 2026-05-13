from dk_unicorn.errors import (
    UnicornCacheError,
    UnicornViewError,
    UnicornAuthenticationError,
    ComponentLoadError,
    ComponentModuleLoadError,
    ComponentClassLoadError,
    RenderNotModifiedError,
    MissingComponentElementError,
    NoRootComponentElementError,
    MultipleRootComponentElementError,
    ComponentNotValidError,
)


def test_unicorn_cache_error():
    err = UnicornCacheError("cache error")
    assert str(err) == "cache error"
    assert isinstance(err, Exception)


def test_unicorn_view_error():
    err = UnicornViewError("view error")
    assert str(err) == "view error"


def test_unicorn_authentication_error():
    err = UnicornAuthenticationError("auth error")
    assert str(err) == "auth error"


def test_component_load_error_with_locations():
    locations = [("module.path", "ClassName")]
    err = ComponentLoadError("not found", locations=locations)
    assert err.locations == locations
    assert str(err) == "not found"


def test_component_load_error_default_locations():
    err = ComponentLoadError("not found")
    assert err.locations == []


def test_component_module_load_error_inherits():
    err = ComponentModuleLoadError("module not found")
    assert isinstance(err, ComponentLoadError)
    assert isinstance(err, Exception)


def test_component_class_load_error_inherits():
    err = ComponentClassLoadError("class not found")
    assert isinstance(err, ComponentLoadError)


def test_render_not_modified_error():
    err = RenderNotModifiedError("not modified")
    assert isinstance(err, Exception)


def test_missing_component_element_error():
    err = MissingComponentElementError("missing element")
    assert isinstance(err, Exception)


def test_no_root_component_element_error():
    err = NoRootComponentElementError("no root")
    assert isinstance(err, Exception)


def test_multiple_root_component_element_error():
    err = MultipleRootComponentElementError("multiple roots")
    assert isinstance(err, Exception)


def test_component_not_valid_error():
    err = ComponentNotValidError("invalid")
    assert isinstance(err, Exception)
