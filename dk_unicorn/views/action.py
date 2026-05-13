from dk_unicorn.call_method_parser import parse_call_method_name


class Action:
    __slots__ = ("action_type", "payload", "partials")

    def __init__(self, data):
        self.action_type = data.get("type", "")
        self.payload = data.get("payload", {})
        self.partials = data.get("partials", [])

        if "partial" in data:
            partial = data["partial"]
            if partial and partial not in self.partials:
                self.partials.append(partial)


class SyncInput(Action):
    __slots__ = ("name", "value")

    def __init__(self, data):
        super().__init__(data)
        self.name = self.payload.get("name", "")
        self.value = self.payload.get("value", "")


class CallMethod(Action):
    __slots__ = ("method_name", "args", "kwargs")

    def __init__(self, data):
        super().__init__(data)
        raw_name = self.payload.get("name", "")
        self.method_name, args, kwargs_proxy = parse_call_method_name(raw_name)
        self.args = args
        self.kwargs = dict(kwargs_proxy)


class Reset(Action):
    pass


class Refresh(Action):
    pass


class Toggle(Action):
    __slots__ = ("method_name", "args", "kwargs")

    def __init__(self, data):
        super().__init__(data)
        raw_name = self.payload.get("name", "")
        self.method_name, self.args, kwargs_proxy = parse_call_method_name(raw_name)
        self.kwargs = dict(kwargs_proxy)
