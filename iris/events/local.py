from iris.events.base import BaseEventSystem


class LocalEventSystem(BaseEventSystem):
    def __init__(self, **kwargs):
        super(LocalEventSystem, self).__init__(**kwargs)
        self.subscriptions = {}

    def subscribe(self, container, event_type):
        self.subscriptions.setdefault(event_type, []).append(container)

    def unsubscribe(self, container, event_type):
        self.subscriptions[event_type].remove(container)

    def emit(self, container, event):
        for container in self.subscriptions.get(event.evt_type, ()):
            container.handle_event(event)
