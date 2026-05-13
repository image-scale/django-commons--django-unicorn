from django.http.response import HttpResponseRedirect


class HashUpdate:
    def __init__(self, url_hash):
        self.hash = url_hash

    def to_json(self):
        return self.__dict__


class LocationUpdate:
    def __init__(self, redirect, title=None):
        self.redirect = redirect
        self.title = title

    def to_json(self):
        return self.__dict__


class PollUpdate:
    def __init__(self, *, timing=None, method=None, disable=False):
        self.timing = timing
        self.method = method
        self.disable = disable

    def to_json(self):
        return self.__dict__
