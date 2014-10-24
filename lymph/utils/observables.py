# Taken from https://github.com/delivero/lymph-storage/blob/master/lymph/storage/observables.py
class Observable(object):
    def __init__(self):
        self.observers = {}

    def notify_observers(self, action, *args, **kwargs):
        for callback in self.observers.get(action, ()):
            callback(*args, **kwargs)

    def observe(self, action, callback):
        self.observers.setdefault(action, []).append(callback)
