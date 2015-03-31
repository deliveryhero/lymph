import gevent

from kazoo.client import KazooClient
from kazoo.handlers.gevent import SequentialGeventHandler

from lymph.core.decorators import rpc
from lymph.core.interfaces import Interface
from lymph.discovery.zookeeper import ZookeeperServiceRegistry
from lymph.events.null import NullEventSystem
from lymph.testing import LymphIntegrationTestCase


class Upper(Interface):
    service_type = 'upper'

    @rpc()
    def upper(self, text=None):
        return text.upper()


class ZookeeperIntegrationTest(LymphIntegrationTestCase):
    use_zookeeper = True

    def setUp(self):
        super(ZookeeperIntegrationTest, self).setUp()
        self.events = NullEventSystem()

        self.upper_container, interface = self.create_container(Upper, 'upper')
        self.lymph_client = self.create_client()

    def create_registry(self, **kwargs):
        zkclient = KazooClient(self.hosts, handler=SequentialGeventHandler())
        return ZookeeperServiceRegistry(zkclient)

    def test_lookup(self):
        service = self.lymph_client.container.lookup('upper')
        self.assertEqual(len(service), 1)
        self.assertEqual(list(service)[0].endpoint, self.upper_container.endpoint)

    def test_upper(self):
        reply = self.lymph_client.request('upper', 'upper.upper', {'text': 'foo'})
        self.assertEqual(reply.body, 'FOO')

    def test_ping(self):
        reply = self.lymph_client.request('upper', 'lymph.ping', {'payload': 42})
        self.assertEqual(reply.body, 42)

    def test_status(self):
        reply = self.lymph_client.request('upper', 'lymph.status', {})
        self.assertEqual(reply.body, {
            'endpoint': self.upper_container.endpoint,
            'identity': self.upper_container.identity,
        })

    def test_get_metrics(self):
        reply = self.lymph_client.request('upper', 'lymph.get_metrics', {})
        self.assertIsInstance(reply.body, list)

    def test_connection_loss(self):
        service = self.lymph_client.container.lookup('upper')
        self.assertEqual(
            [i.identity for i in service],
            [self.upper_container.identity],
        )
        self.upper_container.service_registry.client.stop()
        self.upper_container.service_registry.client.start()
        gevent.sleep(.1)  # XXX: give zk a chance to reconnect
        self.assertEqual(
            [i.identity for i in service],
            [self.upper_container.identity],
        )
