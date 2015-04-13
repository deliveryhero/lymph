import unittest

import gevent
import six

from kazoo.handlers.gevent import SequentialGeventHandler
from kazoo.testing.harness import KazooTestHarness

from lymph.core.container import ServiceContainer
from lymph.core.connection import Connection
from lymph.core.interfaces import Interface
from lymph.core.rpc import ZmqRPCServer
from lymph.core.messages import Message
from lymph.discovery.static import StaticServiceRegistryHub
from lymph.events.local import LocalEventSystem
from lymph.exceptions import RemoteError
from lymph.client import Client
from lymph.utils.sockets import get_unused_port, create_socket

import werkzeug.test
from werkzeug.wrappers import BaseResponse

from lymph.testing.mock_helpers import RpcMockTestCase, EventMockTestCase


class MockServiceNetwork(object):
    def __init__(self):
        self.service_containers = {}
        self.next_port = 1
        self.discovery_hub = StaticServiceRegistryHub()
        self.events = LocalEventSystem()

    def add_service(self, cls, interface_name=None, **kwargs):
        kwargs.setdefault('ip', '300.0.0.1')
        kwargs.setdefault('port', self.next_port)
        self.next_port += 1
        registry = self.discovery_hub.create_registry()
        container = MockServiceContainer(registry=registry, events=self.events, **kwargs)
        container.install_interface(cls, name=interface_name)
        self.service_containers[container.endpoint] = container
        container._mock_network = self
        return container

    def start(self):
        for container in six.itervalues(self.service_containers):
            container.start()

    def stop(self, **kwargs):
        for container in six.itervalues(self.service_containers):
            container.stop()

    def join(self):
        for container in six.itervalues(self.service_containers):
            container.join()


class MockRPCServer(ZmqRPCServer):
    def __init__(self, *args, **kwargs):
        super(MockRPCServer, self).__init__(*args, **kwargs)
        self._bind()

    def _bind(self):
        self.endpoint = 'mock://%s:%s' % (self.ip, self.port)

    def _close_sockets(self):
        pass

    def connect(self, endpoint):
        if endpoint not in self.connections:
            self.connections[endpoint] = Connection(self, endpoint)
        return self.connections[endpoint]

    def _send_message(self, address, msg):
        dst = self.container.lookup(address).connect().endpoint
        dst = self.container._mock_network.service_containers[dst]

        # Exercise the msgpack packing and unpacking.
        frames = msg.pack_frames()
        frames.insert(0, self.endpoint.encode('utf-8'))
        msg = Message.unpack_frames(frames)

        dst.server.recv_message(msg)

    def _recv_loop(self):
        pass


class MockServiceContainer(ServiceContainer):
    server_cls = MockRPCServer

    def __init__(self, *args, **kwargs):
        super(MockServiceContainer, self).__init__(*args, **kwargs)
        self.__shared_sockets = {}

    def get_shared_socket_fd(self, port):
        try:
            return self.__shared_sockets[port].fileno()
        except KeyError:
            host_port = get_unused_port()
            sock = create_socket('127.0.0.1:%s' % host_port, inheritable=True)
            self.__shared_sockets[port] = sock
            return sock.fileno()


class LymphIntegrationTestCase(KazooTestHarness):
    use_zookeeper = False

    def setUp(self):
        super(LymphIntegrationTestCase, self).setUp()
        self._containers = []
        if self.use_zookeeper:
            self.setup_zookeeper(handler=SequentialGeventHandler())

    def tearDown(self):
        super(LymphIntegrationTestCase, self).tearDown()
        for container in self._containers:
            container.stop()
        for container in self._containers:
            container.join()
        if self.use_zookeeper:
            self.teardown_zookeeper()

    def create_client(self, **kwargs):
        container, interface = self.create_container(**kwargs)
        return Client(container)

    def create_registry(self, **kwargs):
        return self.registry

    def create_event_system(self, **kwargs):
        return self.events

    def create_container(self, interface_cls=None, interface_name=None, events=None, registry=None, **kwargs):
        if not events:
            events = self.create_event_system(**kwargs)
        if not registry:
            registry = self.create_registry(**kwargs)
        container = ServiceContainer(events=events, registry=registry, **kwargs)
        interface = None
        if interface_cls:
            interface = container.install_interface(interface_cls, name=interface_name)
        container.start()
        self._containers.append(container)
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
        super(LymphServiceTestCase, self).setUp()
        self.network = MockServiceNetwork()
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
        super(LymphServiceTestCase, self).tearDown()
        self.network.stop()
        self.network.join()


class APITestCase(unittest.TestCase):

    interface_name = None

    def setUp(self):
        super(APITestCase, self).setUp()
        self.network = MockServiceNetwork()

        if not self.interface_name:
            self.interface_name = self.test_interface.__name__.lower()

        container = self.network.add_service(self.test_interface, interface_name=self.interface_name)

        webinterface_object = container.installed_interfaces[self.interface_name]
        self.network.start()

        self.client = werkzeug.test.Client(webinterface_object, BaseResponse)

    def tearDown(self):
        super(APITestCase, self).tearDown()
        self.network.stop()


class AsyncTestsMixin(object):
    def wait_for(self, condition, timeout=2):
        with gevent.Timeout(timeout):
            while not condition():
                gevent.sleep(0)  # yield

    def assert_eventually_true(self, condition, message=None, timeout=2):
        if message is None:
            message = "The expected condition didn't happen within %s seconds" % timeout
        try:
            self.wait_for(condition, timeout=timeout)
        except gevent.Timeout:
            self.fail(message)

    def assert_temporarily_true(self, condition, message=None, timeout=2):
        try:
            with gevent.Timeout(timeout):
                while condition():
                    gevent.sleep(0)  # yield
        except gevent.Timeout:
            return
        if message is None:
            message = "The condition wasn't true for %s seconds" % timeout
        self.fail(message)
