from django.http import HttpResponseRedirect

from dk_unicorn.components import UnicornView
from dk_unicorn.components.updaters import HashUpdate, PollUpdate


class FakeComponent(UnicornView):
    template_name = "templates/test_component.html"
    dictionary = {"name": "test"}
    method_count = 0
    check = False
    nested = {"check": False, "another": {"bool": False}}
    method_arg = ""

    def test_method(self):
        self.method_count += 1

    def test_method_args(self, count):
        self.method_count = count

    def test_method_kwargs(self, count=-1):
        self.method_count = count

    def test_return_value(self):
        return "booya"

    def set_flavor(self, value=""):
        self.method_arg = value

    def redirect_action(self):
        return HttpResponseRedirect("/new-page/")

    def hash_action(self):
        return HashUpdate("#section-2")

    def poll_action(self):
        return PollUpdate(timing=3000, method="check_status")


class FakeParentComponent(UnicornView):
    template_name = "templates/test_component.html"
    parent_count = 0

    def parent_method(self):
        self.parent_count += 1
