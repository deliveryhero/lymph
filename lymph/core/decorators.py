import functools

from lymph.core.declarations import Declaration


def raw_rpc():
    def decorator(func):
        func._rpc = True
        return func
    return decorator


def rpc(raises=()):
    def decorator(func):
        @raw_rpc()
        @functools.wraps(func)
        def inner(self, channel, *args, **kwargs):
            try:
                ret = func(self, *args, **kwargs)
            except raises as ex:
                channel.error(type=ex.__class__.__name__, message=str(ex))
            else:
                channel.reply(ret)

        inner.original = func
        return inner
    return decorator


def event(*event_types, **kwargs):
    def decorator(func):
        from lymph.core.events import EventHandler
        if isinstance(func, EventHandler):
            raise TypeError('lymph.event() decorators cannot be stacked')

        def factory(interface):
            return EventHandler(interface, func, event_types, **kwargs)
        return Declaration(factory)
    return decorator

