
class Plugin(object):
    def __init__(self, container, **config):
        self.container = container
        self.config = config


class Hook(object):
    def __init__(self):
        self.callbacks = []

    def install(self, callback):
        self.callbacks.append(callback)

    def __call__(self, *args, **kwargs):
        for callback in self.callbacks:
            callback(*args, **kwargs)
