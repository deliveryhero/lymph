class Declaration(object):
    def __init__(self, factory):
        self.factory = factory

    def install(self, interface):
        component = self.factory(interface)
        interface.components[self] = component
        return component

    def __get__(self, interface, cls):
        if interface is None:
            return self
        return interface.components[self]


def proxy(*args, **kwargs):
    def factory(interface):
        from lymph.core.interfaces import Proxy
        return Proxy(interface.container, *args, **kwargs)
    return Declaration(factory)
