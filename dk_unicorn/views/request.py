from dk_unicorn.errors import UnicornViewError
from dk_unicorn.serializer import JSONDecodeError, loads
from dk_unicorn.utils import generate_checksum
from dk_unicorn.views.action import (
    Action,
    SyncInput,
    CallMethod,
    Reset,
    Refresh,
    Toggle,
)


class ComponentRequest:
    __slots__ = ("action_queue", "body", "data", "epoch", "hash", "id", "key", "name", "request")

    def __init__(self, request, component_name):
        self.request = request
        self.name = component_name

        try:
            body = loads(request.body)
        except JSONDecodeError as e:
            raise UnicornViewError("Body could not be parsed") from e

        if not body:
            raise AssertionError("Invalid JSON body")

        self.body = body
        self.data = body.get("data", {})
        self.id = body.get("id", "")
        self.epoch = body.get("epoch", "")
        self.key = body.get("key", "")
        self.hash = body.get("hash", "")

        meta = body.get("meta", "")
        if isinstance(meta, str) and ":" in meta:
            parts = meta.split(":")
            self.hash = parts[1] if len(parts) > 1 else ""
            self.epoch = parts[2] if len(parts) > 2 else self.epoch

        self.validate_checksum(meta)

        self.action_queue = []
        for action_data in body.get("actionQueue", []):
            action_type = action_data.get("type", "")

            if action_type == "syncInput":
                self.action_queue.append(SyncInput(action_data))
            elif action_type == "callMethod":
                method_name = action_data.get("payload", {}).get("name", "")
                if method_name == "$refresh":
                    self.action_queue.append(Refresh(action_data))
                elif method_name == "$reset":
                    self.action_queue.append(Reset(action_data))
                elif method_name.startswith("$toggle"):
                    self.action_queue.append(Toggle(action_data))
                else:
                    self.action_queue.append(CallMethod(action_data))
            else:
                self.action_queue.append(Action(action_data))

    def validate_checksum(self, meta=None):
        checksum = generate_checksum(self.data)

        if isinstance(meta, str):
            expected = meta.split(":")[0] if ":" in meta else meta
        else:
            expected = meta or ""

        if expected and checksum != expected:
            raise AssertionError("Checksum does not match")
