import logging

from lymph.core.components import Component


logger = logging.getLogger(__name__)


class Plugin(Component):
    def on_interface_installation(self, interface):
        pass


class Hook(object):
    def __init__(self, name='hook'):
        self.name = name
        self.callbacks = []

    def install(self, callback):
        self.callbacks.append(callback)

    def __call__(self, *args, **kwargs):
        for callback in self.callbacks:
            try:
                callback(*args, **kwargs)
            except:
                logger.exception('%s failure', self.name)
