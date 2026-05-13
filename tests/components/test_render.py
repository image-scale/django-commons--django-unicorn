import pytest

from dk_unicorn.components import Component


class RenderableComponent(Component):
    template_name = "templates/test_component.html"
    text = "Hello World"


def test_component_render():
    comp = RenderableComponent(
        component_id="render1",
        component_name="renderable",
    )
    rendered = comp.render()
    assert "unicorn:id" in rendered
    assert "render1" in rendered
    assert "unicorn:name" in rendered
    assert "renderable" in rendered
    assert "unicorn:data" in rendered
    assert "unicorn:meta" in rendered
    assert "unicorn:calls" in rendered


def test_component_render_has_key():
    comp = RenderableComponent(
        component_id="render2",
        component_name="renderable",
        component_key="my-key",
    )
    rendered = comp.render()
    assert "unicorn:key" in rendered
    assert "my-key" in rendered


def test_component_render_content_hash():
    comp = RenderableComponent(
        component_id="render3",
        component_name="renderable",
    )
    comp.render()
    assert hasattr(comp, "_content_hash")
    assert isinstance(comp._content_hash, str)
    assert len(comp._content_hash) == 8


def test_component_render_data_contains_attributes():
    comp = RenderableComponent(
        component_id="render4",
        component_name="renderable",
    )
    rendered = comp.render()
    assert "Hello World" in rendered
    assert "text" in rendered


def test_component_render_calls_empty():
    comp = RenderableComponent(
        component_id="render5",
        component_name="renderable",
    )
    rendered = comp.render()
    assert "[]" in rendered


def test_component_rendered_hook_called():
    rendered_html = []

    class HookComponent(Component):
        template_name = "templates/test_component.html"
        text = "hook test"

        def rendered(self, html):
            rendered_html.append(html)

    comp = HookComponent(
        component_id="hook1",
        component_name="hook-comp",
    )
    comp.render()
    assert len(rendered_html) == 1
    assert "unicorn:id" in rendered_html[0]
