from abc import ABCMeta, abstractmethod
import six

from iris.core.services import Service


@six.add_metaclass(ABCMeta)
class BaseServiceRegistry(object):
    def __init__(self):
        self.cache = {}

    def on_start(self):
        pass

    def on_stop(self):
        pass

    def get(self, container, service_type, **kwargs):
        try:
            service = self.cache[service_type]
        except KeyError:
            service = Service(container, service_type)
            self.lookup(container, service, **kwargs)
            self.cache[service_type] = service
        return service

    def install(self, container):
        pass

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
