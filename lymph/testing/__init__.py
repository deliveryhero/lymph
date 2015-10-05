import abc
import unittest
import warnings

import gevent
import six
import mock

from kazoo.handlers.gevent import SequentialGeventHandler
from kazoo.testing.harness import KazooTestHarness

from lymph.core.container import ServiceContainer
from lymph.core.connection import Connection
from lymph.core.interfaces import Interface, Proxy
from lymph.core.rpc import ZmqRPCServer
from lymph.core.messages import Message
from lymph.core.monitoring.aggregator import Aggregator
from lymph.discovery.static import StaticServiceRegistryHub
from lymph.events.local import LocalEventSystem
from lymph.client import Client
from lymph.utils.sockets import get_unused_port, create_socket

from lymph.testing.mock_helpers import RpcMockTestCase, EventMockTestCase  # noqa

import werkzeug.test
from werkzeug.wrappers import BaseResponse


class MockServiceNetwork(object):
    def __init__(self):
        self.service_containers = {}
        self.next_port = 1
        self.discovery_hub = StaticServiceRegistryHub()
        self.events = LocalEventSystem()

    def add_service(self, cls, interface_name=None, **kwargs):
        port = self.next_port
        self.next_port += 1
        registry = self.discovery_hub.create_registry()
        container = MockServiceContainer(
            registry=registry,
            events=self.events,
            rpc=MockRPCServer(ip='127.0.0.1', port=port, mock_network=self),
            metrics=Aggregator(),
            **kwargs)
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
        self.__mock_network = kwargs.pop('mock_network')
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

    def _send_message(self, endpoint, msg):
        dst = self.__mock_network.service_containers[endpoint]

        # Exercise the msgpack packing and unpacking.
        frames = msg.pack_frames()
        frames.insert(0, self.endpoint.encode('utf-8'))
        msg = Message.unpack_frames(frames)

        dst.server.recv_message(msg)

    def _recv_loop(self):
        pass


class MockServiceContainer(ServiceContainer):
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
        self._containers = []

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
        container = ServiceContainer(
            events=events,
            registry=registry,
            rpc=ZmqRPCServer(),
            metrics=Aggregator(),
            **kwargs)
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
        warnings.warn("deprecated, please use either RPCServiceTestCase or WebServiceTestCase")
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


@six.add_metaclass(abc.ABCMeta)
class RPCServiceTestCase(unittest.TestCase):
    service_config = {}

    def setUp(self):
        super(RPCServiceTestCase, self).setUp()
        self.network = MockServiceNetwork()

        self.container = self.network.add_service(self.service_class, interface_name=self.service_name)
        self.service = self.container.installed_interfaces[self.service_name]
        self.service.apply_config(self.service_config)

        self.network.start()

    @abc.abstractproperty
    def service_class(self):
        pass

    @property
    def service_name(self):
        return self.service_class.__name__

    def get_proxy(self, **kwargs):
        return Proxy(self.container, self.service_name, **kwargs)

    client = property(get_proxy)

    def request(self, *args, **kwargs):
        channel = self.container.send_request(self.service_name, *args, **kwargs)
        return channel.get(timeout=kwargs.get('timeout', 1))

    def emit(self, *args, **kwargs):
        return self.container.emit_event(*args, **kwargs)

    def tearDown(self):
        super(RPCServiceTestCase, self).tearDown()
        self.network.stop()
        self.network.join()


class WebServiceTestCase(RPCServiceTestCase):

    def setUp(self):
        # XXX(Mouad): Gevent master fail n python3 with: name 'dup' is not defined.
        # A workaround is to mock lymph.utils.sockets.create_socket to return
        # a dummy socket for us.
        port = get_unused_port()
        sock = create_socket('127.0.0.1:%s' % port, inheritable=True)
        with mock.patch('lymph.utils.sockets.create_socket', return_value=sock):
            super(WebServiceTestCase, self).setUp()

    @property
    def client(self):
        return werkzeug.test.Client(self.service.application, BaseResponse)


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
