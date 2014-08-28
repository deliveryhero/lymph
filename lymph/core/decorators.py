from lymph.core.events import EventHandler


def rpc():
    def decorator(func):
        func._rpc = True
        return func
    return decorator


def event(*event_types, **kwargs):
    def decorator(func):
        if isinstance(func, EventHandler):
            raise TypeError('lymph.event() decorators cannot be stacked')
        return EventHandler(func, event_types, **kwargs)
    return decorator
