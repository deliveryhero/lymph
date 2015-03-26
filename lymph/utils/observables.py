
class Observable(object):
    def __init__(self):
        self.observers = {}

    def notify_observers(self, action, *args, **kwargs):
        kwargs.setdefault('action', action)
        for callback in self.observers.get(action, ()):
            callback(*args, **kwargs)

    def observe(self, actions, callback):
        if not isinstance(actions, (tuple, list)):
            actions = (actions,)
        for action in actions:
            self.observers.setdefault(action, set()).add(callback)
