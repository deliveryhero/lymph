import lymph
from lymph.core.interfaces import Interface
from lymph.core.messages import Message
from lymph.testing import RPCServiceTestCase
from lymph.exceptions import RemoteError, Nack


class Upper(Interface):
    service_type = 'upper'

    def __init__(self, *args, **kwargs):
        super(Upper, self).__init__(*args, **kwargs)
        self.eventlog = []

    @lymph.rpc()
    def upper(self, text=None):
        return text.upper()

    @lymph.rpc()
    def indirect_upper(self, text=None):
        # Method to test that it's possible to call upper method as
        # you do normally with any method.
        return self.upper(text)

    @lymph.rpc(raises=(ValueError,))
    def fail(self):
        raise ValueError('foobar')

    @lymph.raw_rpc()
    def just_ack(self, channel):
        channel.ack()

    @lymph.rpc()
    def auto_nack(self):
        raise ValueError('auto nack requested')

    @lymph.event('foo')
    def on_foo_event(self, event):
        self.eventlog.append((event.evt_type, event.body))


class BasicMockTest(RPCServiceTestCase):

    service_class = Upper
    service_name = 'upper'

    def test_upper(self):
        reply = self.client.upper(text='foo')
        self.assertEqual(reply, 'FOO')

    def test_indirect_upper(self):
        reply = self.client.indirect_upper(text='foo')
        self.assertEqual(reply, 'FOO')

    def test_ping(self):
        reply = self.request('lymph.ping', {'payload': 42})
        self.assertEqual(reply.body, 42)

    def test_status(self):
        reply = self.request('lymph.status', {})
        self.assertEqual(reply.body, {
            'endpoint': 'mock://127.0.0.1:1',
            'identity': '79ca257817ccccee3ee62997b864b397',
        })

    def test_error(self):
        with self.assertRaisesRegexp(RemoteError, 'foobar'):
            self.client.fail()

    def test_exception_handling(self):
        with self.assertRaises(RemoteError.ValueError):
            self.client.fail()

    def test_ack(self):
        reply = self.request('upper.just_ack', {})
        self.assertIsNone(reply.body)
        self.assertEqual(reply.type, Message.ACK)

    def test_auto_nack(self):
        with self.assertRaises(Nack):
            self.client.auto_nack()

    def test_events(self):
        log = self.service.eventlog
        self.assertEqual(log, [])
        self.emit('foo', {'arg': 42})
        self.assertEqual(log, [('foo', {'arg': 42})])
        self.emit('foo', {'arg': 43})
        self.assertEqual(log, [('foo', {'arg': 42}), ('foo', {'arg': 43})])

    def test_inspect(self):
        proxy = self.get_proxy(namespace='lymph')
        methods = proxy.inspect()['methods']

        self.assertEqual(set(m['name'] for m in methods), set([
            'upper.fail', 'upper.upper', 'upper.auto_nack', 'upper.just_ack',
            'lymph.status', 'lymph.inspect', 'lymph.ping', 'upper.indirect_upper',
            'lymph.get_metrics',
        ]))
