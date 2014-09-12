from abc import ABCMeta, abstractmethod
import six

from lymph.core.services import Service


@six.add_metaclass(ABCMeta)
class BaseServiceRegistry(object):
    def __init__(self):
        self.cache = {}

    def on_start(self):
        pass

    def on_stop(self):
        pass

    def get(self, service_type, **kwargs):
        try:
            service = self.cache[service_type]
        except KeyError:
            service = Service(self.container, service_type)
            self.lookup(service, **kwargs)
            self.cache[service_type] = service
        return service

    def install(self, container):
        self.container = container

    @abstractmethod
    def discover(self, container):
        raise NotImplementedError

    @abstractmethod
    def lookup(self, container, service, watch=False, timeout=1):
        raise NotImplementedError

    @abstractmethod
    def register(self, container, service_type):
        raise NotImplementedError

    @abstractmethod
    def unregister(self, container, service_type):
        raise NotImplementedError
