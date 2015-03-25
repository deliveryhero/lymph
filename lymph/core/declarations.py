from lymph.core.components import Declaration


def proxy(*args, **kwargs):
    def factory(interface):
        from lymph.core.interfaces import Proxy
        return Proxy(interface.container, *args, **kwargs)
    return Declaration(factory)
