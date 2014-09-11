from lymph.events.base import BaseEventSystem


class NullEventSystem(BaseEventSystem):
    def emit(self, event):
        pass
