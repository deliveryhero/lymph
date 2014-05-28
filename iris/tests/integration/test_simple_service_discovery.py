from iris.testing import IrisIntegrationTestCase
from iris.core.decorators import rpc
from iris.core.interfaces import Interface
from iris.services.coordinator import Coordinator
from iris.discovery.service import IrisCoordinatorServiceRegistry
from iris.events.null import NullEventSystem


class Upper(Interface):
    service_type = 'upper'

    @rpc()
    def upper(self, channel, text=None):
        channel.reply(text.upper())


class BasicIntegrationTest(IrisIntegrationTestCase):
    def setUp(self):
        self.registry = IrisCoordinatorServiceRegistry('tcp://127.0.0.1:42222')
        self.events = NullEventSystem()

        self.coordinator, interface = self.create_container(Coordinator, port=42222)
        self.upper_container, interface = self.create_container(Upper, port=42223)
        self.client = self.create_client(port=42224)

    def tearDown(self):
        self.upper_container.stop()
        self.client.container.stop()
        self.coordinator.stop()
        self.upper_container.join()
        self.client.container.join()
        self.coordinator.join()

    def test_lookup(self):
        service = self.client.container.lookup('iris://upper')
        self.assertEqual(len(service), 1)
        self.assertEqual(next(iter(service)).endpoint, 'tcp://127.0.0.1:42223')

    def test_upper(self):
        reply = self.client.request(self.upper_container.endpoint, 'upper.upper', {'text': 'foo'})
        self.assertEqual(reply.body, 'FOO')

    def test_ping(self):
        reply = self.client.request(self.upper_container.endpoint, 'iris.ping', {'payload': 42})
        self.assertEqual(reply.body, 42)

    def test_status(self):
        reply = self.client.request(self.upper_container.endpoint, 'iris.status', {})
        self.assertEqual(reply.body, {
            'endpoint': 'tcp://127.0.0.1:42223',
            'identity': 'b5cc65725b9b87d308058be8f2efc034',
            'config': {},
        })
