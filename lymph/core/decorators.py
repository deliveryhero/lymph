from lymph.core.declarations import declaration


def rpc():
    def decorator(func):
        func._rpc = True
        return func
    return decorator


def event(*event_types, **kwargs):
    def decorator(func):
        from lymph.core.events import EventHandler
        if isinstance(func, EventHandler):
            raise TypeError('lymph.event() decorators cannot be stacked')

        @declaration()
        def factory(interface):
            return EventHandler(interface, func, event_types, **kwargs)
        return factory
    return decorator

