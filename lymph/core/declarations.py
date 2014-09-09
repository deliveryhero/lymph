def declaration(*args, **kwargs):
    def decorator(factory):
        return Declaration(factory, *args, **kwargs)
    return decorator


class Declaration(object):
    def __init__(self, factory, *args, **kwargs):
        self.factory = factory
        self.args = args
        self.kwargs = kwargs

    def install(self, interface):
        interface.components[self] = self.factory(interface, *self.args, **self.kwargs)

    def __get__(self, interface, cls):
        if interface is None:
            return self
        return interface.components[self]
