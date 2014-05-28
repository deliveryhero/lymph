from iris.events.base import BaseEventSystem


class NullEventSystem(BaseEventSystem):
    def emit(self, container, event):
        pass
