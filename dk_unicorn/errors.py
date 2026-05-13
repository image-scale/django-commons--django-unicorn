class UnicornCacheError(Exception):
    pass


class UnicornViewError(Exception):
    pass


class UnicornAuthenticationError(Exception):
    pass


class ComponentLoadError(Exception):
    def __init__(self, message="", locations=None):
        super().__init__(message)
        self.locations = locations or []


class ComponentModuleLoadError(ComponentLoadError):
    pass


class ComponentClassLoadError(ComponentLoadError):
    pass


class RenderNotModifiedError(Exception):
    pass


class MissingComponentElementError(Exception):
    pass


class MissingComponentViewElementError(Exception):
    pass


class NoRootComponentElementError(Exception):
    pass


class MultipleRootComponentElementError(Exception):
    pass


class ComponentNotValidError(Exception):
    pass
