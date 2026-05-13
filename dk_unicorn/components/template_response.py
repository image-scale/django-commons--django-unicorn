import logging
import re
from collections import deque

import orjson
from django.conf import settings
from django.template.backends.django import Template
from django.template.response import TemplateResponse
from lxml import html

from dk_unicorn.errors import (
    MissingComponentElementError,
    MissingComponentViewElementError,
    MultipleRootComponentElementError,
    NoRootComponentElementError,
)
from dk_unicorn.settings import get_minify_html_enabled
from dk_unicorn.signals import component_rendered
from dk_unicorn.utils import generate_checksum

logger = logging.getLogger(__name__)

VOID_ELEMENTS = (
    "<area>", "<base>", "<br>", "<col>", "<embed>", "<hr>",
    "<img>", "<input>", "<link>", "<meta>", "<param>",
    "<source>", "<track>", "<wbr>",
)


def element_to_str(element, **kwargs):
    return html.tostring(element, encoding="unicode", **kwargs)


def is_html_well_formed(html_content):
    tag_list = re.split(r"(<[^>!]*>)", html_content)[1::2]
    stack = deque()

    for tag in tag_list:
        if "/" not in tag:
            cleaned_tag = re.sub(r"(<([\w\-]+)[^>!]*>)", r"<\2>", tag)
            if cleaned_tag not in VOID_ELEMENTS:
                stack.append(cleaned_tag)
        elif len(stack) > 0 and (tag.replace("/", "") == stack[-1]):
            stack.pop()

    return len(stack) == 0


def get_root_element(content):
    if isinstance(content, html.HtmlElement):
        return content

    try:
        if "<html" in content.lower():
            root_element = html.fromstring(content)
        else:
            fragments = html.fragments_fromstring(content)
            elements = [f for f in fragments if isinstance(f, html.HtmlElement) and f.tag != "script"]

            if not elements:
                raise MissingComponentElementError("No root element for the component was found")

            root_element = elements[0]
    except (MissingComponentElementError, MissingComponentViewElementError):
        raise
    except Exception as e:
        raise MissingComponentElementError(f"Failed to parse component HTML: {e}") from e

    if root_element.tag == "html":
        view_element = None
        for element in root_element.iter():
            if "unicorn:view" in element.attrib or "u:view" in element.attrib:
                view_element = element
                break

        if view_element is None:
            raise MissingComponentViewElementError(
                "An element with an `unicorn:view` attribute is required for a direct view"
            )
        return view_element

    return root_element


def assert_has_single_wrapper_element(content, component_name):
    try:
        if isinstance(content, html.HtmlElement):
            elements = [content]
        else:
            fragments = html.fragments_fromstring(content)
            elements = [f for f in fragments if isinstance(f, html.HtmlElement) and (f.tag != "script" or f.attrib)]
    except Exception:
        return

    for element in elements:
        if "unicorn:view" in element.attrib or "u:view" in element.attrib:
            return

    if len(elements) > 1:
        raise MultipleRootComponentElementError(
            f"The '{component_name}' component appears to have multiple root elements."
        )

    if not elements:
        raise NoRootComponentElementError(
            f"The '{component_name}' component does not appear to have one root element."
        )

    if f"<{elements[0].tag}>" in VOID_ELEMENTS:
        raise NoRootComponentElementError(
            f"The '{component_name}' component root element cannot be a void element like <{elements[0].tag}>."
        )


class ComponentTemplateResponse(TemplateResponse):
    def __init__(
        self,
        template,
        request,
        *,
        context=None,
        content_type=None,
        status=None,
        charset=None,
        using=None,
        component=None,
        init_js=False,
        epoch="",
        **kwargs,
    ):
        super().__init__(
            template=template,
            request=request,
            context=context,
            content_type=content_type,
            status=status,
            charset=charset,
            using=using,
        )
        self.component = component
        self.init_js = init_js
        self.epoch = epoch or ""

    def resolve_template(self, template):
        if isinstance(template, (list, tuple)):
            if isinstance(template[0], Template):
                return template[0]
        return super().resolve_template(template)

    def render(self):
        response = super().render()

        if not self.component or not self.component.component_id:
            return response

        content = response.content.decode("utf-8")

        if settings.DEBUG and not is_html_well_formed(content):
            logger.warning(
                f"The HTML in '{self.component.component_name}' appears to be missing a closing tag."
            )

        try:
            assert_has_single_wrapper_element(content, self.component.component_name)
        except (NoRootComponentElementError, MultipleRootComponentElementError) as ex:
            logger.warning(ex)

        root_element = get_root_element(content)

        frontend_context_variables = self.component.get_frontend_context_variables()
        frontend_context_variables_dict = orjson.loads(frontend_context_variables)
        data_checksum = generate_checksum(frontend_context_variables_dict)

        root_element.set("unicorn:id", self.component.component_id)
        root_element.set("unicorn:name", self.component.component_name)
        root_element.set("unicorn:key", str(self.component.component_key or ""))
        root_element.set("unicorn:data", frontend_context_variables)
        root_element.set("unicorn:calls", orjson.dumps(self.component.calls).decode("utf-8"))

        rendered_no_checksum = element_to_str(root_element)
        content_hash = generate_checksum(rendered_no_checksum)
        self.component._content_hash = content_hash

        root_element.set("unicorn:meta", data_checksum)

        rendered_template = element_to_str(root_element)

        self.component.rendered(rendered_template)
        component_rendered.send(
            sender=self.component.__class__,
            component=self.component,
            html=rendered_template,
        )
        response.content = rendered_template

        if get_minify_html_enabled():
            try:
                from htmlmin import minify
                minified = minify(response.content.decode())
                if len(minified) < len(rendered_template):
                    response.content = minified
            except ImportError:
                pass

        return response
