import gevent

from lymph.core.events import EventDispatcher
from lymph.events.base import BaseEventSystem


class LocalEventSystem(BaseEventSystem):
    def __init__(self, **kwargs):
        super(LocalEventSystem, self).__init__(**kwargs)
        self.dispatcher = EventDispatcher()

    def subscribe(self, handler, **kwargs):
        for event_type in handler.event_types:
            self.dispatcher.register(event_type, handler)

    def unsubscribe(self, handler):
        raise NotImplementedError()

    def emit(self, event, delay=0):
        if delay:
            gevent.spawn_later(delay, self.dispatcher, event)
        else:
            self.dispatcher(event)
