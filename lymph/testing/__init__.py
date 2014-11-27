import six
import unittest

from kazoo.handlers.gevent import SequentialGeventHandler
from kazoo.testing.harness import KazooTestHarness

from lymph.core.container import ServiceContainer
from lymph.core.connection import Connection
from lymph.core.interfaces import Interface
from lymph.core.messages import Message
from lymph.discovery.static import StaticServiceRegistryHub
from lymph.events.local import LocalEventSystem
from lymph.client import Client
from lymph.services.coordinator import Coordinator

import werkzeug.test
from werkzeug.wrappers import BaseResponse

class MockServiceNetwork(object):
    def __init__(self):
        self.service_containers = {}
        self.next_port = 0
        self.discovery_hub = StaticServiceRegistryHub()
        self.events = LocalEventSystem()

    def add_service(self, cls, interface_name=None, **kwargs):
        kwargs.setdefault('ip', '300.0.0.1')
        kwargs.setdefault('port', self.next_port)
        self.next_port += 1
        registry = self.discovery_hub.create_registry()
        container = MockServiceContainer(registry=registry, events=self.events, **kwargs)
        container.install(cls, interface_name=interface_name)
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

        # Exercise the msgpack packing and unpacking.
        frames = msg.pack_frames()
        frames.insert(0, self.endpoint.encode('utf-8'))
        msg = Message.unpack_frames(frames)

        dst.recv_message(msg)

    def recv_loop(self):
        pass


class LymphIntegrationTestCase(KazooTestHarness):
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

    def create_container(self, interface_cls=None, interface_name=None, **kwargs):
        kwargs.setdefault('events', self.events)
        kwargs.setdefault('registry', self.registry)
        container = ServiceContainer(**kwargs)
        interface = None
        if interface_cls:
            interface = container.install(interface_cls, interface_name=interface_name)
        container.start()
        return container, interface


class ClientInterface(Interface):
    service_type = 'client'


class LymphServiceTestCase(unittest.TestCase):
    client_class = ClientInterface
    client_name = 'client'
    client_config = {}
    service_class = ClientInterface
    service_name = 'client'
    service_config = {}

    def setUp(self):
        self.network = MockServiceNetwork()
        self.coordinator = self.network.add_service(Coordinator)
        self.service_container = self.network.add_service(
            self.service_class,
            interface_name=self.service_name
        )
        self.service = self.service_container.installed_interfaces[
            self.service_name
        ]
        self.service.apply_config(self.service_config)
        self.client_container = self.network.add_service(
            self.client_class,
            interface_name=self.client_name
        )
        self.client = self.client_container.installed_interfaces[
            self.client_name
        ]
        self.client.apply_config(self.client_config)
        self.network.start()

    def tearDown(self):
        self.network.stop()
        self.network.join()


class APITestCase(unittest.TestCase):

    interface_name = None

    def setUp(self):
        self.network = MockServiceNetwork()

        if not self.interface_name:
            self.interface_name = self.test_interface.__name__.lower()

        container = self.network.add_service(self.test_interface, interface_name = self.interface_name)

        webinterface_object = container.installed_interfaces[self.interface_name]
        webinterface_object.configure({'ip' : 'localhost'})
        self.network.start()

        self.client = werkzeug.test.Client(webinterface_object, BaseResponse)

    def tearDown(self):
        self.network.stop()
