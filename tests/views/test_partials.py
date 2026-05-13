from unittest.mock import MagicMock, PropertyMock

import orjson

from dk_unicorn.views.response import ComponentResponse


def _make_component(rendered_html, component_id="test-id", component_name="test"):
    component = MagicMock()
    component.component_id = component_id
    component.component_name = component_name
    component.component_key = ""
    component.calls = []
    component.children = []
    component.errors = {}
    component.parent = None
    component.get_frontend_context_variables.return_value = orjson.dumps({"key": "val"}).decode()
    component.render.return_value = rendered_html
    return component


def _make_request():
    req = MagicMock()
    req.hash = ""
    return req


def test_partial_by_unicorn_key():
    html_content = '<div><span unicorn:key="section-1">Hello</span><span>Other</span></div>'
    component = _make_component(html_content)
    request = _make_request()

    partials = [{"key": "section-1"}]
    response = ComponentResponse(component, request, partials=partials)
    data = response.get_data()

    assert "partials" in data
    assert len(data["partials"]) == 1
    assert data["partials"][0]["key"] == "section-1"
    assert "Hello" in data["partials"][0]["dom"]


def test_partial_by_id():
    html_content = '<div><span id="my-section">Content</span></div>'
    component = _make_component(html_content)
    request = _make_request()

    partials = [{"id": "my-section"}]
    response = ComponentResponse(component, request, partials=partials)
    data = response.get_data()

    assert "partials" in data
    assert len(data["partials"]) == 1
    assert data["partials"][0]["id"] == "my-section"
    assert "Content" in data["partials"][0]["dom"]


def test_partial_by_target():
    html_content = '<div><span unicorn:key="target-1">Found</span></div>'
    component = _make_component(html_content)
    request = _make_request()

    partials = [{"target": "target-1"}]
    response = ComponentResponse(component, request, partials=partials)
    data = response.get_data()

    assert "partials" in data
    assert data["partials"][0]["key"] == "target-1"


def test_partial_not_found():
    html_content = '<div><span>No keys here</span></div>'
    component = _make_component(html_content)
    request = _make_request()

    partials = [{"key": "nonexistent"}]
    response = ComponentResponse(component, request, partials=partials)
    data = response.get_data()

    assert "partials" not in data or len(data.get("partials", [])) == 0


def test_no_partials():
    html_content = '<div>Simple</div>'
    component = _make_component(html_content)
    request = _make_request()

    response = ComponentResponse(component, request, partials=[])
    data = response.get_data()

    assert "partials" not in data


def test_multiple_partials():
    html_content = '<div><span unicorn:key="a">A</span><span unicorn:key="b">B</span></div>'
    component = _make_component(html_content)
    request = _make_request()

    partials = [{"key": "a"}, {"key": "b"}]
    response = ComponentResponse(component, request, partials=partials)
    data = response.get_data()

    assert "partials" in data
    assert len(data["partials"]) == 2


def test_partial_root_element_match():
    html_content = '<div unicorn:key="root-key">Root content</div>'
    component = _make_component(html_content)
    request = _make_request()

    partials = [{"key": "root-key"}]
    response = ComponentResponse(component, request, partials=partials)
    data = response.get_data()

    assert "partials" in data
    assert data["partials"][0]["key"] == "root-key"
