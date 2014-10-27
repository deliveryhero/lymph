import unittest

import lymph
from lymph.core.interfaces import Interface
from lymph.core.messages import Message
from lymph.services.coordinator import Coordinator
from lymph.testing import MockServiceNetwork
from lymph.exceptions import ErrorReply, Nack


class Upper(Interface):
    service_type = 'upper'

    def __init__(self, *args, **kwargs):
        super(Upper, self).__init__(*args, **kwargs)
        self.eventlog = []

    @lymph.rpc()
    def upper(self, channel, text=None):
        channel.reply(text.upper())

    @lymph.rpc()
    def fail(self, channel):
        channel.error(type="RuntimeError", errno=42)

    @lymph.rpc()
    def just_ack(self, channel):
        channel.ack()

    @lymph.rpc()
    def auto_nack(self, channel):
        raise ValueError('auto nack requested')

    @lymph.event('foo')
    def on_foo_event(self, event):
        self.eventlog.append((event.evt_type, event.body))


class ClientInterface(Interface):
    service_type = 'client'


class BasicMockTest(unittest.TestCase):
    def setUp(self):
        self.network = MockServiceNetwork()
        self.coordinator = self.network.add_service(Coordinator, port=42400)
        self.upper_container = self.network.add_service(Upper)
        self.client_container = self.network.add_service(ClientInterface)
        self.network.start()
        self.client = self.client_container.installed_interfaces['client']

    def tearDown(self):
        self.network.stop()
        self.network.join()

    def test_upper(self):
        reply = self.client.request('upper', 'upper.upper', {'text': 'foo'})
        self.assertEqual(reply.body, 'FOO')

    def test_ping(self):
        reply = self.client.request('upper', 'lymph.ping', {'payload': 42})
        self.assertEqual(reply.body, 42)

    def test_status(self):
        reply = self.client.request(self.upper_container.endpoint, 'lymph.status', {})
        self.assertEqual(reply.body, {
            'endpoint': 'mock://300.0.0.1:1',
            'identity': '252946e723b6b07c1f5f0aa9442fb348',
            'config': {},
        })

    def test_error(self):
        self.assertRaises(ErrorReply, self.client.request, self.upper_container.endpoint, 'upper.fail', {})

    def test_ack(self):
        reply = self.client.request(self.upper_container.endpoint, 'upper.just_ack', {})
        self.assertIsNone(reply.body)
        self.assertEqual(reply.type, Message.ACK)

    def test_auto_nack(self):
        self.assertRaises(Nack, self.client.request, self.upper_container.endpoint, 'upper.auto_nack', {})

    def test_events(self):
        log = self.upper_container.installed_interfaces['upper'].eventlog
        self.assertEqual(log, [])
        self.client.emit('foo', {'arg': 42})
        self.assertEqual(log, [('foo', {'arg': 42})])
        self.client.emit('foo', {'arg': 43})
        self.assertEqual(log, [('foo', {'arg': 42}), ('foo', {'arg': 43})])

    def test_proxy(self):
        proxy = self.client.proxy('upper')
        self.assertEqual(proxy.upper(text='foo'), 'FOO')

    def test_inspect(self):
        proxy = self.client.proxy('upper', namespace='lymph')
        methods = proxy.inspect()['methods']
        self.assertEqual(set(m['name'] for m in methods), set([
            'upper.fail', 'upper.upper', 'upper.auto_nack', 'upper.just_ack',
            'lymph.status', 'lymph.inspect', 'lymph.ping',
        ]))
