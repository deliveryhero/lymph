from .base import BaseServiceRegistry, SERVICE_NAMESPACE
from lymph.exceptions import LookupFailure


class StaticServiceRegistryHub(object):
    def __init__(self):
        self.registry = {}

    def create_registry(self):
        return StaticServiceRegistry(self)

    def lookup(self, service, **kwargs):
        service_name = service.name
        try:
            instances = self.registry[service_name]
            for data in instances:
                service.update(data.get('id'), **data)
        except KeyError:
            raise LookupFailure()
        return service

    def register(self, service_name, instance, namespace=SERVICE_NAMESPACE):
        if namespace != SERVICE_NAMESPACE:
            return
        self.registry.setdefault(service_name, []).append(instance.serialize())

    def unregister(self, service_name, instance, namespace=SERVICE_NAMESPACE):
        if namespace != SERVICE_NAMESPACE:
            return
        self.registry.get(service_name, []).remove(instance.serialize())

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

    def register(self, service_name, instance, **kwargs):
        return self.hub.register(service_name, instance, **kwargs)

    def unregister(self, service_name, instance, **kwargs):
        return self.hub.unregister(service_name, instance, **kwargs)
