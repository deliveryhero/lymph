import unittest

from lymph.exceptions import RemoteError
from lymph.core.interfaces import Proxy
from lymph.core.container import ServiceContainer

import mock

import hamcrest


class MockMixins(object):

    def _assert_equal_calls(self, actual_calls, expected_calls):
        actual_count, expected_count = len(actual_calls), len(expected_calls)

        self.assertEqual(
            expected_count, actual_count,
            msg="number of calls doesn't match, expected %d actual %d" % (expected_count, actual_count))

        for pos, (actual_call, expected_call) in enumerate(zip(actual_calls, expected_calls)):
            self._assert_equal_call(actual_call, expected_call, pos)

    def _assert_equal_call(self, actual_call, expected_call, position):
        act_name, act_args, act_kwargs = self._unpack_mock_call(actual_call)
        exp_name, exp_args, exp_kwargs = self._unpack_mock_call(expected_call)

        self.assertEqual(
            exp_name, act_name,
            msg="function #%d name doesn't match, expected %s actual %s" % (position, exp_name, act_name))

        self._assert_equal_arguments(act_args, exp_args, act_name, position)
        self._assert_equal_keyword_arguments(act_kwargs, exp_kwargs, act_name, position)

    @staticmethod
    def _unpack_mock_call(mock_call):
        # Since we are using the syntax mock.call('<func_name>', arg1, arg2, kw1=val1),
        # in this case the unpacking of mock.call will put the <func_name> in args[0] and not
        # in the first unpacked element.
        _, args, kwargs = mock_call
        name, args = args[0], args[1:]
        return name, args, kwargs

    def _assert_equal_arguments(self, actual_args, expected_args, function_name, position):
        self.assertEqual(
            len(actual_args), len(expected_args),
            msg="call #%d '%s' arguments count doesn't match, expected %r actual %r" % (position, function_name, len(expected_args), len(actual_args)))

        for actual_arg, expected_arg in zip(actual_args, expected_args):
            hamcrest.assert_that(actual_arg, hamcrest.is_(expected_arg))

    def _assert_equal_keyword_arguments(self, actual_kwargs, expected_kwargs, function_name, position):
        actual_arg_names = sorted(actual_kwargs.keys())
        expected_arg_names = sorted(expected_kwargs.keys())

        self.assertEqual(
            actual_arg_names, expected_arg_names,
            msg="call #%d '%s' keyword arguments doesn't match, expected %r actual %r" % (position, function_name, expected_arg_names, actual_arg_names))

        for name, act_value in actual_kwargs.items():
            hamcrest.assert_that(act_value, hamcrest.is_(expected_kwargs[name]))


def _get_side_effect(mocks):
    class ProxyCall(object):
        def __init__(self, data):
            self.data = data

        def __call__(self, name, **kwargs):
            try:
                result = self.data[name]
                if isinstance(result, Exception):
                    raise getattr(RemoteError, result.__class__.__name__)('', '')
                if callable(result):
                    return result(**kwargs)
                return result
            except KeyError:
                return

        def update(self, func_name, new_value):
            self.data[func_name] = new_value
    return ProxyCall(mocks)


class RpcMockTestCase(unittest.TestCase, MockMixins):
    def setUp(self):
        super(RpcMockTestCase, self).setUp()
        self.rpc_patch = mock.patch.object(Proxy, '_call')
        self.rpc_mock = self.rpc_patch.start()

    def tearDown(self):
        super(RpcMockTestCase, self).tearDown()
        self.rpc_patch.stop()

    def setup_rpc_mocks(self, mocks):
        self.rpc_mock.side_effect = _get_side_effect(mocks)

    def update_rpc_mock(self, func_name, new_value):
        self.rpc_mock.side_effect.update(func_name, new_value)

    @property
    def rpc_mock_calls(self):
        return self.rpc_mock.mock_calls

    def assert_rpc_calls(self, *expected_calls):
        self._assert_equal_calls(self.rpc_mock_calls, expected_calls)


class EventMockTestCase(unittest.TestCase, MockMixins):
    def setUp(self):
        super(EventMockTestCase, self).setUp()
        self.event_patch = mock.patch.object(ServiceContainer, 'emit_event')
        self.event_mock = self.event_patch.start()

    def tearDown(self):
        super(EventMockTestCase, self).tearDown()
        self.event_patch.stop()

    @property
    def events(self):
        return self.event_mock.mock_calls

    def assert_events_emitted(self, *expected_emitted):
        self._assert_equal_calls(self.events, expected_emitted)

    def _assert_equal_keyword_arguments(self, actual_kwargs, expected_kwargs, function_name, position):
        if 'delay' not in expected_kwargs:
            expected_kwargs['delay'] = 0
        super(EventMockTestCase, self)._assert_equal_keyword_arguments(actual_kwargs, expected_kwargs, function_name, position)
