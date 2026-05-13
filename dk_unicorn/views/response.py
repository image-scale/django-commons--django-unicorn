import orjson

from dk_unicorn.components.template_response import get_root_element, element_to_str
from dk_unicorn.errors import RenderNotModifiedError
from dk_unicorn.serializer import dumps as json_dumps
from dk_unicorn.signals import component_parent_rendered
from dk_unicorn.utils import generate_checksum


class ComponentResponse:
    __slots__ = ("component", "component_request", "return_data", "partials")

    def __init__(self, component, component_request, return_data=None, partials=None):
        self.component = component
        self.component_request = component_request
        self.return_data = return_data
        self.partials = partials

    def _collect_all_calls(self):
        calls = list(self.component.calls)
        for child in self.component.children:
            calls.extend(child.calls)
        return calls

    def get_data(self):
        frontend_vars = self.component.get_frontend_context_variables()
        frontend_vars_dict = orjson.loads(frontend_vars)
        data_checksum = generate_checksum(frontend_vars_dict)

        all_calls = self._collect_all_calls()

        result = {
            "id": self.component.component_id,
            "data": frontend_vars_dict,
            "errors": self.component.errors,
            "calls": [{"fn": c["fn"], "args": list(c.get("args", ()))} for c in all_calls],
            "meta": {"checksum": data_checksum},
        }

        rendered = self.component.render()

        if hasattr(self.component, "_content_hash"):
            rendered_hash = self.component._content_hash
            request_hash = getattr(self.component_request, "hash", "")

            if (
                rendered_hash == request_hash
                and not self.return_data
                and not all_calls
            ):
                raise RenderNotModifiedError("Render not modified")

        root_element = get_root_element(rendered)
        root_element.set("unicorn:meta", data_checksum)
        result["dom"] = element_to_str(root_element)

        if self.return_data:
            result["return"] = self.return_data
            if hasattr(self.return_data, "get"):
                if self.return_data.get("redirect"):
                    result["redirect"] = self.return_data["redirect"]
                if self.return_data.get("poll"):
                    result["poll"] = self.return_data["poll"]

        if self.component.parent and self.component.parent.force_render:
            parent_rendered = self.component.parent.render()
            self.component.parent_rendered(parent_rendered)
            component_parent_rendered.send(
                sender=self.component.parent.__class__,
                component=self.component.parent,
                html=parent_rendered,
            )
            result["parent"] = {"id": self.component.parent.component_id, "dom": parent_rendered}
            result.pop("dom", None)

        return result
