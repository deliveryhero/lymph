from lymph.events.base import BaseEventSystem


class NullEventSystem(BaseEventSystem):
    def emit(self, event, delay=0):
        pass
