import os
from .base import BaseServiceRegistry
from lymph.exceptions import LookupFailure, RegistrationFailure, Timeout
from lymph.core.decorators import rpc
from lymph.core.interfaces import Interface


class SimpleCoordinatorClient(Interface):
    @rpc()
    def notice(self, channel, service_type=None, instances=None):
        self.container.update_service(service_type, instances)


class LymphCoordinatorServiceRegistry(BaseServiceRegistry):
    def __init__(self, coordinator_endpoint, container=None):
        super(LymphCoordinatorServiceRegistry, self).__init__()
        self.coordinator_endpoint = coordinator_endpoint

    @classmethod
    def from_config(cls, config, **kwargs):
        coordinator_endpoint = config.get('coordinator_endpoint', os.environ.get('IRIS_COORDINATOR', None))
        return cls(coordinator_endpoint=coordinator_endpoint)

    def install(self, container):
        super(LymphCoordinatorServiceRegistry, self).install(container)
        container.install(SimpleCoordinatorClient)

    def register(self, service_type, timeout=1):
        body = self.container.get_instance_description()
        body['service_type'] = service_type
        channel = self.container.send_request(self.coordinator_endpoint, 'coordinator.register', body)
        try:
            channel.get(timeout=timeout)
        except Timeout:
            raise RegistrationFailure()

    def unregister(self, service_type, timeout=1):
        pass

    def discover(self):
        channel = self.container.send_request(self.coordinator_endpoint, 'coordinator.discover', {})
        try:
            msg = channel.get()
        except Timeout:
            raise LookupFailure(None, "couldn't reach the coordinator")
        return msg.body

    def lookup(self, service, timeout=1):
        channel = self.container.send_request(self.coordinator_endpoint, 'coordinator.lookup', {
            'service_type': service.service_type,
        })
        try:
            msg = channel.get()
        except Timeout:
            raise LookupFailure(None, "lookup of %s timed out" % service.service_type)
        if not msg.body:
            raise LookupFailure(None, "failed to resolve %s" % service.service_type)
        for info in msg.body:
            identity = info.pop('identity')
            service.update(identity, **info)
