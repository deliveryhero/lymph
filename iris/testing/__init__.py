import six

from kazoo.handlers.gevent import SequentialGeventHandler
from kazoo.testing.harness import KazooTestHarness

from iris.core.container import ServiceContainer
from iris.core.connection import Connection
from iris.discovery.static import StaticServiceRegistry
from iris.events.local import LocalEventSystem
from iris.client import Client


class MockServiceNetwork(object):
    def __init__(self):
        self.service_containers = {}
        self.next_port = 0
        self.registry = StaticServiceRegistry({})
        self.events = LocalEventSystem()

    def add_service(self, cls, **kwargs):
        kwargs.setdefault('ip', '300.0.0.1')
        kwargs.setdefault('port', self.next_port)
        self.next_port += 1
        container = MockServiceContainer(registry=self.registry, events=self.events, **kwargs)
        container.install(cls)
        self.service_containers[container.endpoint] = container
        container._mock_network = self
        return container

    def start(self):
        for container in six.itervalues(self.service_containers):
            container.start()

    def stop(self):
        for container in six.itervalues(self.service_containers):
            container.stop()

    def join(self):
        for container in six.itervalues(self.service_containers):
            container.join()


class MockServiceContainer(ServiceContainer):
    def bind(self):
        self.endpoint = 'mock://%s:%s' % (self.ip, self.port)

    def close_sockets(self):
        pass

    def connect(self, endpoint):
        if endpoint not in self.connections:
            self.connections[endpoint] = Connection(self, endpoint)
        return self.connections[endpoint]

    def send_message(self, address, msg):
        dst = self.lookup(address).connect().endpoint
        dst = self._mock_network.service_containers[dst]
        dst.recv_message(msg)

    def recv_loop(self):
        pass

    def handle_event(self, event):
        # FIXME: we dispatch events synchronously to make them recordable
        self.dispatch_event(event)


class IrisIntegrationTestCase(KazooTestHarness):
    use_zookeeper = False

    def setUp(self):
        if self.use_zookeeper:
            self.setup_zookeeper(handler=SequentialGeventHandler())

    def tearDown(self):
        if self.use_zookeeper:
            self.teardown_zookeeper()

    def create_client(self, **kwargs):
        container, interface = self.create_container(**kwargs)
        return Client(container)

    def create_container(self, interface_cls=None, **kwargs):
        kwargs.setdefault('events', self.events)
        kwargs.setdefault('registry', self.registry)
        container = ServiceContainer(**kwargs)
        interface = None
        if interface_cls:
            interface = container.install(interface_cls)
        container.start()
        return container, interface
