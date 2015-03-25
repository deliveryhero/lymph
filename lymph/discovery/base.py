import abc
import six

from lymph.core.services import Service
from lymph.core.components import Component


@six.add_metaclass(abc.ABCMeta)
class BaseServiceRegistry(Component):
    def __init__(self):
        super(BaseServiceRegistry, self).__init__()
        self.cache = {}

    def get(self, service_name, **kwargs):
        try:
            service = self.cache[service_name]
        except KeyError:
            service = Service(self.container, name=service_name)
            self.lookup(service, **kwargs)
            self.cache[service_name] = service
        return service

    def install(self, container):
        self.container = container

    @abc.abstractmethod
    def discover(self):
        raise NotImplementedError

    @abc.abstractmethod
    def lookup(self, container, service, watch=False, timeout=1):
        raise NotImplementedError

    @abc.abstractmethod
    def register(self, container, service_name):
        raise NotImplementedError

    @abc.abstractmethod
    def unregister(self, container, service_name):
        raise NotImplementedError
