import uuid
import kombu

import lymph

from lymph.events.kombu import KombuEventSystem
from lymph.discovery.static import StaticServiceRegistryHub
from lymph.testing import LymphIntegrationTestCase, AsyncTestsMixin


class TestInterface(lymph.Interface):
    def __init__(self, *args, **kwargs):
        super(TestInterface, self).__init__(*args, **kwargs)
        self.collected_events = []

    @lymph.event('foo')
    def on_foo(self, event):
        self.collected_events.append(event)

    @lymph.event('foo_broadcast', broadcast=True)
    def on_foo_broadcast(self, event):
        self.collected_events.append(event)


class TestEventBroadcastInterface(lymph.Interface):
    def __init__(self, *args, **kwargs):
        super(TestEventBroadcastInterface, self).__init__(*args, **kwargs)
        self.collected_events = []

    @lymph.event('foo_broadcast', broadcast=True)
    def on_foo_broadcast(self, event):
        self.collected_events.append(event)


class KombuIntegrationTest(LymphIntegrationTestCase, AsyncTestsMixin):
    use_zookeeper = False

    def setUp(self):
        super(KombuIntegrationTest, self).setUp()
        self.exchange_name = 'test-%s' % uuid.uuid4()
        self.discovery_hub = StaticServiceRegistryHub()

        self.the_container, self.the_interface = self.create_container(TestInterface, 'test')
        self.the_container_broadcast, self.the_interface_broadcast = self.create_container(TestEventBroadcastInterface, 'test')
        self.lymph_client = self.create_client()

    def tearDown(self):
        super(KombuIntegrationTest, self).tearDown()
        connection = self.get_kombu_connection()
        exchange = kombu.Exchange(self.exchange_name)
        exchange(connection).delete()

        # FIXME: there should be a better way to get this exchange name
        waiting_exchange = kombu.Exchange('%s_waiting' % self.exchange_name)
        waiting_exchange(connection).delete()

        # FIXME: there should be a better way to get the queue names
        for name in ('foo-wait_500', 'test-on_foo'):
            queue = kombu.Queue(name)
            queue(connection).delete()

    def get_kombu_connection(self):
        return kombu.Connection(transport='amqp', host='127.0.0.1')

    def create_event_system(self, **kwargs):
        return KombuEventSystem(self.get_kombu_connection(), self.exchange_name)

    def create_registry(self, **kwargs):
        return self.discovery_hub.create_registry(**kwargs)

    def received_check(self, n):
        def check():
            return len(self.the_interface.collected_events) == n
        return check

    def received_broadcast_check(self, n):
        def check():
            return (len(self.the_interface.collected_events) + len(self.the_interface_broadcast.collected_events)) == n
        return check

    def test_emit(self):
        self.lymph_client.emit('foo', {})
        self.assert_eventually_true(self.received_check(1), timeout=10)
        self.assertEqual(self.the_interface.collected_events[0].evt_type, 'foo')

    def test_delayed_emit(self):
        self.lymph_client.emit('foo', {}, delay=.5)
        self.assert_temporarily_true(self.received_check(0), timeout=.2)
        self.assert_eventually_true(self.received_check(1), timeout=10)
        self.assertEqual(self.the_interface.collected_events[0].evt_type, 'foo')

    def test_broadcast_event(self):
        self.lymph_client.emit('foo_broadcast', {})
        self.assert_eventually_true(self.received_broadcast_check(2), timeout=10)
        self.assertEqual(self.the_interface.collected_events[0].evt_type, 'foo_broadcast')
        self.assertEqual(self.the_interface_broadcast.collected_events[0].evt_type, 'foo_broadcast')
