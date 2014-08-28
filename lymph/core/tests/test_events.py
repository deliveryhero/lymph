import unittest

from lymph.core.events import EventDispatcher


class EventDispatcherTest(unittest.TestCase):
    def setUp(self):
        self.dispatcher = EventDispatcher()
        self.handler_log = []
        self.handlers = {}

    def make_handler(self, name):
        if name in self.handlers:
            return self.handlers[name]

        def handler(*args):
            self.handler_log.append((name, args))

        handler.__name__ = name
        self.handlers[name] = handler
        return handler

    def assert_dispatched_patterns_equal(self, event_type, patterns):
        self.assertEqual(
            set(pattern for pattern, handler in self.dispatcher.dispatch(event_type)),
            set(patterns),
        )

    def assert_dispatched_handlers_equal(self, event_type, handlers):
        self.assertEqual(
            set(handler.__name__ for pattern, handler in self.dispatcher.dispatch(event_type)),
            set(handlers),
        )

    def test_basic_dispatch(self):
        self.dispatcher.register('foo', self.make_handler('foo'))
        self.dispatcher.register('bar', self.make_handler('bar'))
        self.dispatcher.register('foo.bar', self.make_handler('foo2'))

        self.assert_dispatched_patterns_equal('foo', {'foo'})
        self.assert_dispatched_patterns_equal('bar', {'bar'})
        self.assert_dispatched_patterns_equal('fooo', [])
        self.assert_dispatched_patterns_equal('foofoo', [])
        self.assert_dispatched_patterns_equal('', [])

    def test_wildcard_dispatch(self):
        self.dispatcher.register('foo', self.make_handler('foo'))
        self.dispatcher.register('#', self.make_handler('hash'))
        self.dispatcher.register('*', self.make_handler('star'))
        self.dispatcher.register('foo.*', self.make_handler('foo_star'))
        self.dispatcher.register('foo.#', self.make_handler('foo_hash'))

        self.assert_dispatched_patterns_equal('foo', {'foo', '*', '#'})
        self.assert_dispatched_patterns_equal('foo.bar', {'#', 'foo.*', 'foo.#'})
        self.assert_dispatched_patterns_equal('foo.bar.baz', {'#', 'foo.#'})
        self.assert_dispatched_patterns_equal('', {'#'})

    def test_multi_pattern_registration(self):
        self.dispatcher.register('foo', self.make_handler('foo'))
        self.dispatcher.register('#', self.make_handler('foo'))

        self.assert_dispatched_patterns_equal('foo', {'foo', '#'})
        self.assert_dispatched_handlers_equal('foo', {'foo'})

    def test_update(self):
        self.dispatcher.register('foo', self.make_handler('base_foo'))
        self.dispatcher.register('#', self.make_handler('hash'))

        ed = EventDispatcher()
        ed.register('foo', self.make_handler('foo'))
        ed.register('bar', self.make_handler('bar'))
        self.dispatcher.update(ed)

        self.assert_dispatched_handlers_equal('foo', {'foo', 'base_foo', 'hash'})
        self.assert_dispatched_handlers_equal('bar', {'hash', 'bar'})
