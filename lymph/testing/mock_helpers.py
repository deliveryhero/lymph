import unittest
import functools

from lymph.exceptions import RemoteError
from lymph.core.interfaces import Proxy
from lymph.core.container import ServiceContainer

import mock

import hamcrest


class MockMixins(object):

    def _assert_equal_calls(self, actual_calls, expected_calls):
        actual_count, expected_count = len(actual_calls), len(expected_calls)

        # TODO(Mouad): Add in the message which calls are missing.
        self.assertEqual(
            expected_count, actual_count,
            msg="number of calls doesn't match, expected %d actual %d" % (expected_count, actual_count))

        for pos, (actual_call, expected_call) in enumerate(zip(actual_calls, expected_calls)):
            success, msg = self._check_equal_call(actual_call, expected_call)
            if not success:
                self.fail("function #%d %s" % (pos, msg))

    def _check_equal_call(self, actual_call, expected_call):
        act_name, act_args, act_kwargs = self._unpack_mock_call(actual_call)
        exp_name, exp_args, exp_kwargs = self._unpack_mock_call(expected_call)

        if exp_name != act_name:
            return False, "name doesn't match, expected %r actual %r" % (exp_name, act_name)

        success, msg = self._check_equal_arguments(act_args, exp_args)
        if not success:
            return False, msg
        return self._check_equal_keyword_arguments(act_kwargs, exp_kwargs)

    @staticmethod
    def _unpack_mock_call(mock_call):
        # Since we are using the syntax mock.call('<func_name>', arg1, arg2, kw1=val1),
        # in this case the unpacking of mock.call will put the <func_name> in args[0] and not
        # in the first unpacked element.
        _, args, kwargs = mock_call
        name, args = args[0], args[1:]
        return name, args, kwargs

    def _check_equal_arguments(self, actual_args, expected_args):
        if len(actual_args) != len(expected_args):
            return False, "arguments count doesn't match, expected %r actual %r" % (len(expected_args), len(actual_args))

        for pos, (actual_arg, expected_arg) in enumerate(zip(actual_args, expected_args)):
            success, msg = self._check_that(actual_arg, hamcrest.is_(expected_arg))
            if not success:
                return False, "argument #%d doesn't match, %s" % (pos, msg)
        return True, None

    def _check_equal_keyword_arguments(self, actual_kwargs, expected_kwargs):
        actual_arg_names = sorted(actual_kwargs.keys())
        expected_arg_names = sorted(expected_kwargs.keys())

        if actual_arg_names != expected_arg_names:
            return False, "keyword arguments doesn't match, expected %r actual %r" % (expected_arg_names, actual_arg_names)

        for name, act_value in actual_kwargs.items():
            success, msg = self._check_that(act_value, hamcrest.is_(expected_kwargs[name]))
            if not success:
                return False, "keyword argument %r doesn't match, %s" % (name, msg)
        return True, None

    @staticmethod
    def _check_that(actual, expected):
        try:
            hamcrest.assert_that(actual, expected)
        except AssertionError as ex:
            msg = ex.args[0]
            return False, msg
        return True, None

    def _assert_equal_any_calls(self, actual_calls, expected_calls):
        next_idx = 0
        for exp_call in expected_calls:
            name, _, _ = self._unpack_mock_call(exp_call)
            possible_matches = self._get_same_named_calls(actual_calls, name, start_idx=next_idx)
            if not possible_matches:
                self.fail("Call '%r' wasn't found." % (exp_call, ))
            elif len(possible_matches) == 1:
                # In case we have one possible match, use _assert_equal_calls to have
                # a better error message.
                match_idx, actual_call = possible_matches[0]
                self._assert_equal_calls([actual_call], [exp_call])
            else:
                match_idx = self._assert_match_one_call(possible_matches, exp_call)
            next_idx = match_idx + 1

    def _get_same_named_calls(self, actual_calls, name, start_idx=0):
        matches = []
        for i, act_call in enumerate(actual_calls[start_idx:]):
            act_name, _, _ = self._unpack_mock_call(act_call)
            if name == act_name:
                matches.append((i + start_idx, act_call))
        return matches

    def _assert_match_one_call(self, actual_calls, exp_call):
        for idx, act_call in actual_calls:
            success, _ = self._check_equal_call(act_call, exp_call)
            if success:
                return idx
        msg = "Call '%r' wasn't found." % (exp_call, )
        if actual_calls:
            msg += " Maybe you want: \n%s" % "\n".join(map(str, actual_calls))
        self.fail(msg)


def _get_rpc_mock(rpc_mocks=None, original=Proxy._call):
    class ProxyCall(mock.MagicMock):

        rpc_functions = rpc_mocks or {}

        def __call__(self, proxy_inst, __name, **kwargs):
            # XXX (Mouad): We need to call MagicMock __call__ here else calls
            # will not be tracked, and we do it for all calls mocked or not.
            super(ProxyCall, self).__call__(__name, **kwargs)
            try:
                result = self.rpc_functions[__name]
            except KeyError:
                return original(proxy_inst, __name, **kwargs)
            else:
                if isinstance(result, Exception):
                    raise getattr(RemoteError, result.__class__.__name__)('', '')
                if callable(result):
                    return result(**kwargs)
                return result

        def __get__(self, obj, type=None):
            return functools.partial(self.__call__, obj)
    return ProxyCall()


class RpcMockTestCase(unittest.TestCase, MockMixins):
    def setUp(self):
        super(RpcMockTestCase, self).setUp()
        self.rpc_patch = mock.patch.object(Proxy, '_call', new_callable=_get_rpc_mock)
        self.rpc_mock = self.rpc_patch.start()

    def tearDown(self):
        super(RpcMockTestCase, self).tearDown()
        self.rpc_patch.stop()

    def setup_rpc_mocks(self, rpc_functions):
        self.rpc_mock.rpc_functions.update(rpc_functions)

    def update_rpc_mock(self, func_name, return_value):
        self.rpc_mock.rpc_functions[func_name] = return_value

    def delete_rpc_mock(self, func_name):
        del self.rpc_mock.rpc_functions[func_name]

    @property
    def rpc_mock_calls(self):
        return self.rpc_mock.mock_calls

    def assert_rpc_calls(self, *expected_calls):
        self._assert_equal_calls(self.rpc_mock_calls, expected_calls)

    def assert_any_rpc_calls(self, *expected_calls):
        self._assert_equal_any_calls(self.rpc_mock_calls, expected_calls)


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
        expected_emitted_with_delay = []
        for call in expected_emitted:
            name, args, kwargs = self._unpack_mock_call(call)
            kwargs.setdefault('delay', 0)
            expected_emitted_with_delay.append(mock.call(name, *args, **kwargs))
        self._assert_equal_calls(self.events, expected_emitted_with_delay)
