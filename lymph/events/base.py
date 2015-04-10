import abc
import six

from lymph.core.components import Component


@six.add_metaclass(abc.ABCMeta)
class BaseEventSystem(Component):
    @classmethod
    def from_config(cls, config, **kwargs):
        return cls(**kwargs)

    def install(self, container):
        self.container = container

    def on_start(self):
        pass

    def on_stop(self, **kwargs):
        pass

    def subscribe(self, handler):
        raise NotImplementedError

    def unsubscribe(self, handler):
        raise NotImplementedError

    @abc.abstractmethod
    def emit(self, event, delay=0):
        raise NotImplementedError
