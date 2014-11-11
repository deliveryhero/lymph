from lymph.testing import LymphIntegrationTestCase
from lymph.core.decorators import rpc
from lymph.core.interfaces import Interface
from lymph.services.coordinator import Coordinator
from lymph.discovery.static import StaticServiceRegistry
from lymph.events.null import NullEventSystem


class Upper(Interface):
    service_type = 'upper'

    @rpc()
    def upper(self, text=None):
        return text.upper()


class BasicIntegrationTest(LymphIntegrationTestCase):
    def setUp(self):
        self.registry = StaticServiceRegistry()
        self.events = NullEventSystem()

        self.coordinator, interface = self.create_container(Coordinator)
        self.upper_container, interface = self.create_container(Upper)
        self.client = self.create_client()

    def tearDown(self):
        self.upper_container.stop()
        self.client.container.stop()
        self.coordinator.stop()
        self.upper_container.join()
        self.client.container.join()
        self.coordinator.join()

    def test_lookup(self):
        service = self.client.container.lookup('upper')
        self.assertEqual(len(service), 1)
        self.assertEqual(next(iter(service)).endpoint, self.upper_container.endpoint)

    def test_upper(self):
        reply = self.client.request(self.upper_container.endpoint, 'upper.upper', {'text': 'foo'})
        self.assertEqual(reply.body, 'FOO')

    def test_ping(self):
        reply = self.client.request(self.upper_container.endpoint, 'lymph.ping', {'payload': 42})
        self.assertEqual(reply.body, 42)

    def test_status(self):
        reply = self.client.request(self.upper_container.endpoint, 'lymph.status', {})
        self.assertEqual(reply.body['endpoint'], self.upper_container.endpoint)
        self.assertEqual(reply.body['config'], {})
