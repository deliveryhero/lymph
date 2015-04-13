import unittest

import mock

from lymph.testing.mock_helpers import MockMixins


class DummyTestCase(unittest.TestCase, MockMixins):

    def runTest(self):
        pass


class RPCMockHelperTests(unittest.TestCase):

    def setUp(self):
        self.dummy_case = DummyTestCase()

    def test_single_call_match(self):
        self.dummy_case._assert_equal_calls(
            [mock.call('func', 1, foo='bar')],
            [mock.call('func', 1, foo='bar')]
        )

    def test_single_call_args_mismatch(self):
        with self.assertRaises(AssertionError):
            self.dummy_case._assert_equal_calls(
                [mock.call('func', 1, foo='bar')],
                [mock.call('func', 102, foo='bar')]
            )

    def test_single_call_keyword_value_mismatch(self):
        with self.assertRaises(AssertionError):
            self.dummy_case._assert_equal_calls(
                [mock.call('func', 1, foo='foobar')],
                [mock.call('func', 1, foo='bar')]
            )

    def test_single_call_keyword_name_mismatch(self):
        with self.assertRaises(AssertionError):
            self.dummy_case._assert_equal_calls(
                [mock.call('func', 1, foo='bar')],
                [mock.call('func', 1, somthing='bar')]
            )

    def test_multiple_call_match(self):
        self.dummy_case._assert_equal_calls(
            [
                mock.call('func', 1, foo='foo'),
                mock.call('func', 2, foo='bar'),
                mock.call('func', 3, foo='foobar')
            ],
            [
                mock.call('func', 1, foo='foo'),
                mock.call('func', 2, foo='bar'),
                mock.call('func', 3, foo='foobar')
            ],
        )
