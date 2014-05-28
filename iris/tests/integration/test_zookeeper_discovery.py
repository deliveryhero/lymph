from iris.core.decorators import rpc
from iris.core.interfaces import Interface
from iris.discovery.zookeeper import ZookeeperServiceRegistry
from iris.events.null import NullEventSystem
from iris.testing import IrisIntegrationTestCase


class Upper(Interface):
    service_type = 'upper'

    @rpc()
    def upper(self, channel, text=None):
        channel.reply(text.upper())


class ZookeeperIntegrationTest(IrisIntegrationTestCase):
    use_zookeeper = True

    def setUp(self):
        super(ZookeeperIntegrationTest, self).setUp()
        self.registry = ZookeeperServiceRegistry(self.hosts)
        self.events = NullEventSystem()

        self.upper_container, interface = self.create_container(Upper)
        self.iris_client = self.create_client(port=42224)

    def tearDown(self):
        self.upper_container.stop()
        self.iris_client.container.stop()
        self.upper_container.join()
        self.iris_client.container.join()
        super(ZookeeperIntegrationTest, self).tearDown()

    def test_lookup(self):
        service = self.iris_client.container.lookup('iris://upper')
        self.assertEqual(len(service), 1)
        self.assertEqual(next(iter(service)).endpoint, self.upper_container.endpoint)

    def test_upper(self):
        reply = self.iris_client.request(self.upper_container.endpoint, 'upper.upper', {'text': 'foo'})
        self.assertEqual(reply.body, 'FOO')

    def test_ping(self):
        reply = self.iris_client.request(self.upper_container.endpoint, 'iris.ping', {'payload': 42})
        self.assertEqual(reply.body, 42)

    def test_status(self):
        reply = self.iris_client.request(self.upper_container.endpoint, 'iris.status', {})
        self.assertEqual(reply.body, {
            'endpoint': self.upper_container.endpoint,
            'identity': self.upper_container.identity,
            'config': {},
        })
