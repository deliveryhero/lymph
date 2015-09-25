import unittest

import blessings
import gevent
import six

from lymph.cli.testing import CliIntegrationTestCase, CliTestMixin
from lymph.core.decorators import rpc
from lymph.core.interfaces import Interface


class Upper(Interface):

    @rpc()
    def upper(self, text=None):
        return text.upper()


class RequestCommandTests(CliIntegrationTestCase):
    def setUp(self):
        super(RequestCommandTests, self).setUp()
        self.upper_container, interface = self.create_container(Upper, 'upper')

    def test_request(self):
        result = self.cli(['request', 'upper.upper', '{"text":"foo"}'])
        self.assertEqual(result.returncode, 0)
        output = "u'FOO'" if six.PY2 else "'FOO'"
        self.assertEqual(result.stdout.rstrip(), output)

    def test_negative_request(self):
        result = self.cli(['request', 'no_exiting_container', '{}'])
        self.assertEqual(result.returncode, 1)

    def test_inspect(self):
        # Use --no-color to facilitate string comparison.
        result = self.cli(['inspect', '--no-color', 'upper'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('upper.upper(text)', result.stdout)

    def test_negative_inspect(self):
        result = self.cli(['inspect', 'no_existing_container'])
        self.assertEqual(result.returncode, 1)


class ListCommandTests(CliTestMixin, unittest.TestCase):
    def test_list(self):
        self.assert_lines_equal(['list'], u"""
            {t.bold}config     {t.normal}Prints configuration for inspection
            {t.bold}tail       {t.normal}Streams the log output of services to stderr
            {t.bold}emit       {t.normal}Emits an event in the event system
            {t.bold}request    {t.normal}Sends a single RPC request to a service and outputs the response
            {t.bold}inspect    {t.normal}Describes the RPC interface of a service
            {t.bold}discover   {t.normal}Shows available services
            {t.bold}help       {t.normal}Displays help information about lymph
            {t.bold}list       {t.normal}Lists all available commands
            {t.bold}subscribe  {t.normal}Subscribes to event types and prints occurences on stdout
            {t.bold}instance   {t.normal}Runs a single service instance
            {t.bold}node       {t.normal}Runs a node service that manages a group of processes on the same machine
            {t.bold}shell      {t.normal}Starts an interactive Python shell, locally or remotely
            {t.bold}worker     {t.normal}Runs a worker instance
        """.format(t=blessings.Terminal()), config=False)


class HelpCommandTests(CliTestMixin, unittest.TestCase):
    def test_help(self):
        self.assert_first_line_equals(['help'], 'Usage: lymph [options] <command> [<args>...]', config=False)

    def test_help_list(self):
        self.assert_first_line_equals(['help', 'list'], 'Usage: lymph list [options]', config=False)


class ServiceCommandTests(CliIntegrationTestCase):
    def test_instance(self):
        self.cli_config['interfaces'] = {
            'echo': {
                'class': 'lymph.tests.integration.test_cli:Upper',
            }
        }
        command_greenlet = gevent.spawn(self.cli, ['instance'])
        client = self.create_client()
        gevent.sleep(1)  # FIXME: how can we wait for the instance to register?
        response = client.request('echo', 'echo.upper', {'text': 'hi'}, timeout=1)
        self.assertEqual(response.body, 'HI')
        command_greenlet.kill()
        command_greenlet.join()
