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
        self.registry = ZookeeperServiceRegistry(self.hosts)
        self.events = NullEventSystem()

        self.upper_container, interface = self.create_container(Upper)
        self.lymph_client = self.create_client()

    def tearDown(self):
        self.upper_container.stop()
        self.lymph_client.container.stop()
        self.upper_container.join()
        self.lymph_client.container.join()
        super(ZookeeperIntegrationTest, self).tearDown()

    def test_lookup(self):
        service = self.lymph_client.container.lookup('upper')
        self.assertEqual(len(service), 1)
        self.assertEqual(next(iter(service)).endpoint, self.upper_container.endpoint)

    def test_upper(self):
        reply = self.lymph_client.request(self.upper_container.endpoint, 'upper.upper', {'text': 'foo'})
        self.assertEqual(reply.body, 'FOO')

    def test_ping(self):
        reply = self.lymph_client.request(self.upper_container.endpoint, 'lymph.ping', {'payload': 42})
        self.assertEqual(reply.body, 42)

    def test_status(self):
        reply = self.lymph_client.request(self.upper_container.endpoint, 'lymph.status', {})
        self.assertEqual(reply.body, {
            'endpoint': self.upper_container.endpoint,
            'identity': self.upper_container.identity,
            'config': {},
        })
