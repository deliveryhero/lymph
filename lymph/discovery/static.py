from .base import BaseServiceRegistry
from lymph.exceptions import LookupFailure


class StaticServiceRegistryHub(object):
    def __init__(self):
        self.containers = []
        self.registry = {}

    def create_registry(self):
        return StaticServiceRegistry(self)

    def lookup(self, service, **kwargs):
        service_type = service.service_type
        try:
            containers = self.registry[service_type]
            for container in containers:
                service.update(container.identity, endpoint=container.endpoint)
        except KeyError:
            raise LookupFailure(None)
        return service

    def register(self, service_type, container):
        self.registry.setdefault(service_type, []).append(container)

    def unregister(self, service_type, container):
        self.registry.get(service_type, []).remove(container)

    def discover(self):
        return list(self.registry.keys())


class StaticServiceRegistry(BaseServiceRegistry):
    def __init__(self, hub=None):
        super(StaticServiceRegistry, self).__init__()
        self.hub = hub or StaticServiceRegistryHub()

    def discover(self):
        return self.hub.discover()

    def lookup(self, service, **kwargs):
        return self.hub.lookup(service, **kwargs)

    def register(self, service_type):
        return self.hub.register(service_type, self.container)

    def unregister(self, service_type):
        return self.hub.unregister(service_type, self.container)
