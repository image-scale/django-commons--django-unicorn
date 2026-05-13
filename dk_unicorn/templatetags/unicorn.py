import shortuuid
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from dk_unicorn.call_method_parser import InvalidKwargError, parse_kwarg
from dk_unicorn.errors import ComponentNotValidError

register = template.Library()


@register.inclusion_tag("unicorn/scripts.html")
def unicorn_scripts():
    from dk_unicorn.settings import get_setting

    csrf_header_name = settings.CSRF_HEADER_NAME
    if csrf_header_name.startswith("HTTP_"):
        csrf_header_name = csrf_header_name[5:]
    csrf_header_name = csrf_header_name.replace("_", "-")
    csrf_cookie_name = settings.CSRF_COOKIE_NAME

    return {
        "MINIFIED": get_setting("MINIFIED", not settings.DEBUG),
        "CSRF_HEADER_NAME": csrf_header_name,
        "CSRF_COOKIE_NAME": csrf_cookie_name,
    }


@register.inclusion_tag("unicorn/errors.html", takes_context=True)
def unicorn_errors(context):
    return {"unicorn": {"errors": context.get("unicorn", {}).get("errors", {})}}


def unicorn(parser, token):
    contents = token.split_contents()

    if len(contents) < 2:
        first_arg = token.contents.split()[0]
        raise template.TemplateSyntaxError(f"{first_arg} tag requires at least a single argument")

    component_name = parser.compile_filter(contents[1])

    args = []
    kwargs = {}
    unparseable_kwargs = {}

    for arg in contents[2:]:
        try:
            parsed_kwarg = parse_kwarg(arg, raise_if_unparseable=True)
            kwargs.update(parsed_kwarg)
        except InvalidKwargError:
            if not kwargs:
                args.append(arg)
        except ValueError:
            parsed_kwarg = parse_kwarg(arg, raise_if_unparseable=False)
            unparseable_kwargs.update(parsed_kwarg)

    return ComponentNode(component_name, args, kwargs, unparseable_kwargs)


class ComponentNode(template.Node):
    def __init__(self, component_name, args=None, kwargs=None, unparseable_kwargs=None):
        self.component_name = component_name
        self.args = args or []
        self.kwargs = kwargs or {}
        self.unparseable_kwargs = unparseable_kwargs or {}
        self.component_key = ""
        self.parent = None

    def render(self, context):
        request = None
        if hasattr(context, "request"):
            request = context.request

        from dk_unicorn.components import UnicornView

        resolved_args = []
        for value in self.args:
            resolved_arg = template.Variable(value).resolve(context)
            resolved_args.append(resolved_arg)

        resolved_kwargs = self.kwargs.copy()

        for key, value in self.unparseable_kwargs.items():
            try:
                resolved_value = template.Variable(value).resolve(context)
                resolved_kwargs[key] = resolved_value
            except (TypeError, template.VariableDoesNotExist):
                resolved_kwargs[key] = value

        if "key" in resolved_kwargs:
            self.component_key = resolved_kwargs.pop("key")

        if "parent" in resolved_kwargs:
            self.parent = resolved_kwargs.pop("parent")
        else:
            try:
                implicit_parent = template.Variable("unicorn.component").resolve(context)
                if implicit_parent:
                    self.parent = implicit_parent
            except template.VariableDoesNotExist:
                pass

        unicorn_stub = ""
        if not self.parent and not context.get("unicorn_stub_rendered"):
            unicorn_stub = mark_safe("<script>window.Unicorn = window.Unicorn || {};</script>\n")
            context["unicorn_stub_rendered"] = True

        try:
            component_name = self.component_name.resolve(context)
        except AttributeError as e:
            raise ComponentNotValidError(f"Component template is not valid: {self.component_name}.") from e

        component_id = None

        if self.parent:
            component_id = f"{self.parent.component_id}:{component_name}"
            if self.component_key:
                component_id = f"{component_id}:{self.component_key}"
            elif "id" in resolved_kwargs:
                component_id = f"{component_id}:{resolved_kwargs['id']}"
            elif "pk" in resolved_kwargs:
                component_id = f"{component_id}:{resolved_kwargs['pk']}"

        if component_id:
            if not settings.DEBUG:
                component_id = shortuuid.uuid(name=component_id)[:8]
        else:
            component_id = shortuuid.uuid()[:8]

        self.component_id = component_id

        self.view = UnicornView.create(
            component_id=component_id,
            component_name=component_name,
            component_key=self.component_key,
            parent=self.parent,
            request=request,
            component_args=resolved_args,
            kwargs=resolved_kwargs,
        )

        extra_context = {}
        for c in context:
            extra_context.update(c)

        rendered_component = self.view.render(init_js=True, extra_context=extra_context)
        return unicorn_stub + rendered_component


register.tag("unicorn", unicorn)
