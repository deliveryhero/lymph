from .base import BaseServiceRegistry
from iris.exceptions import LookupFailure


class StaticServiceRegistry(BaseServiceRegistry):
    def __init__(self, registry):
        super(StaticServiceRegistry, self).__init__()
        self.registry = registry

    def discover(self, container):
        return list(self.registry.keys())

    def lookup(self, container, service, watch=True, timeout=0):
        service_type = service.service_type
        try:
            containers = self.registry[service_type]
            for container in containers:
                service.update(container.identity, endpoint=container.endpoint)
        except KeyError:
            raise LookupFailure(None)
        return service

    def register(self, container, service_type):
        self.registry.setdefault(service_type, []).append(container)

    def unregister(self, container, service_type):
        self.registry.get(service_type, []).remove(container)
