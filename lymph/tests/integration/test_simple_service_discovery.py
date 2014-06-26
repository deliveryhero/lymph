from lymph.testing import LymphIntegrationTestCase
from lymph.core.decorators import rpc
from lymph.core.interfaces import Interface
from lymph.services.coordinator import Coordinator
from lymph.discovery.service import LymphCoordinatorServiceRegistry
from lymph.events.null import NullEventSystem


class Upper(Interface):
    service_type = 'upper'

    @rpc()
    def upper(self, channel, text=None):
        channel.reply(text.upper())


class BasicIntegrationTest(LymphIntegrationTestCase):
    def setUp(self):
        self.registry = LymphCoordinatorServiceRegistry('tcp://127.0.0.1:42222')
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
        service = self.client.container.lookup('lymph://upper')
        self.assertEqual(len(service), 1)
        self.assertEqual(next(iter(service)).endpoint, 'tcp://127.0.0.1:42223')

    def test_upper(self):
        reply = self.client.request(self.upper_container.endpoint, 'upper.upper', {'text': 'foo'})
        self.assertEqual(reply.body, 'FOO')

    def test_ping(self):
        reply = self.client.request(self.upper_container.endpoint, 'lymph.ping', {'payload': 42})
        self.assertEqual(reply.body, 42)

    def test_status(self):
        reply = self.client.request(self.upper_container.endpoint, 'lymph.status', {})
        self.assertEqual(reply.body, {
            'endpoint': 'tcp://127.0.0.1:42223',
            'identity': 'b5cc65725b9b87d308058be8f2efc034',
            'config': {},
        })
