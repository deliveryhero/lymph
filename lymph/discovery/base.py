import abc
import six

from lymph.core.services import Service
from lymph.core.components import Component


@six.add_metaclass(abc.ABCMeta)
class BaseServiceRegistry(Component):
    def __init__(self, **kwargs):
        super(BaseServiceRegistry, self).__init__(**kwargs)
        self.cache = {}

    def get(self, service_name, **kwargs):
        try:
            service = self.cache[service_name]
        except KeyError:
            service = Service(name=service_name)
            self.lookup(service, **kwargs)
            self.cache[service_name] = service
        return service

    @abc.abstractmethod
    def discover(self):
        raise NotImplementedError

    @abc.abstractmethod
    def lookup(self, service, timeout=1):
        raise NotImplementedError

    @abc.abstractmethod
    def register(self, service_name, instance):
        raise NotImplementedError

    @abc.abstractmethod
    def unregister(self, service_name, instance):
        raise NotImplementedError
