import logging

from django.http.response import HttpResponseRedirect

from dk_unicorn.components.updaters import HashUpdate, LocationUpdate, PollUpdate
from dk_unicorn.serializer import dumps, loads

logger = logging.getLogger(__name__)


class Return:
    def __init__(self, method_name, args=None, kwargs=None):
        self.method_name = method_name
        self.args = args or []
        self.kwargs = kwargs or {}
        self._value = {}
        self.redirect = {}
        self.poll = {}

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

        if value is not None:
            if isinstance(value, HttpResponseRedirect):
                self.redirect = {"url": value.url}
            elif isinstance(value, HashUpdate):
                self.redirect = {"hash": value.hash}
            elif isinstance(value, LocationUpdate):
                self.redirect = {
                    "url": value.redirect.url,
                    "refresh": True,
                    "title": value.title,
                }
            elif isinstance(value, PollUpdate):
                self.poll = value.to_json()

            if self.redirect:
                self._value = self.redirect

    def get_data(self):
        try:
            serialized_value = loads(dumps(self.value))
            serialized_args = loads(dumps(self.args))
            serialized_kwargs = loads(dumps(self.kwargs))

            return {
                "method": self.method_name,
                "args": serialized_args,
                "kwargs": serialized_kwargs,
                "value": serialized_value,
            }
        except Exception as e:
            logger.exception(e)

        return {}
