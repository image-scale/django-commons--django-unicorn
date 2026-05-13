from django.test import RequestFactory

from dk_unicorn.components import UnicornView


class SafeFieldComponent(UnicornView):
    template_name = "test.html"
    content = "<b>Bold</b>"
    name = "Alice"

    class Meta:
        safe = ("content",)


class DispatchComponent(UnicornView):
    template_name = "templates/test_component.html"
    greeting = "Hello"

    def mount(self):
        self.greeting = "Mounted"


def test_handle_safe_fields():
    c = SafeFieldComponent(component_name="test", component_id="123")
    c._handle_safe_fields()
    from django.utils.safestring import SafeString
    assert isinstance(c.content, SafeString)
    assert c.content == "<b>Bold</b>"


def test_handle_safe_fields_non_safe_unchanged():
    c = SafeFieldComponent(component_name="test", component_id="123")
    c._handle_safe_fields()
    assert not hasattr(c.name, "__html__")


def test_handle_safe_fields_no_meta():
    c = UnicornView(component_name="test", component_id="123")
    c.template_name = "test.html"
    c._handle_safe_fields()


def test_dispatch():
    rf = RequestFactory()
    request = rf.get("/")
    c = DispatchComponent(component_name="test", component_id="123")
    response = c.dispatch(request)
    assert response is not None


def test_as_view():
    view = DispatchComponent.as_view(component_name="test")
    assert callable(view)


def test_as_view_auto_generates_id():
    view = DispatchComponent.as_view(component_name="test")
    rf = RequestFactory()
    request = rf.get("/")
    response = view(request)
    assert response is not None
