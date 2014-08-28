from abc import ABCMeta, abstractmethod
import six


@six.add_metaclass(ABCMeta)
class BaseEventSystem(object):
    @classmethod
    def from_config(cls, config, **kwargs):
        return cls(**kwargs)

    def install(self, container):
        pass

    def on_start(self):
        pass

    def on_stop(self):
        pass

    def subscribe(self, container, handler):
        raise NotImplementedError

    def unsubscribe(self, container, handler):
        raise NotImplementedError

    @abstractmethod
    def emit(self, container, event):
        raise NotImplementedError
