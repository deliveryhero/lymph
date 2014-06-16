import unittest
import gevent


from iris.cli.testing import CliIntegrationTestCase, CliTestMixin
from iris.core.decorators import rpc
from iris.core.interfaces import Interface


class Upper(Interface):
    service_type = 'upper'

    @rpc()
    def upper(self, channel, text=None):
        channel.reply(text.upper())


class RequestCommandTests(CliIntegrationTestCase):
    def setUp(self):
        super(RequestCommandTests, self).setUp()
        self.upper_container, interface = self.create_container(Upper, port=42223)

    def tearDown(self):
        self.upper_container.stop()
        self.upper_container.join()
        super(RequestCommandTests, self).tearDown()

    def test_request(self):
        stdout = self.cli(['request', 'iris://upper', 'upper.upper', '{"text":"foo"}'])
        self.assertEqual(stdout, 'FOO\n')


class ListCommandTests(CliTestMixin, unittest.TestCase):
    def test_list(self):
        self.assert_lines_equal(['list'], """
            tail              Stream the logs of one or more services.
            emit              Manually emits an event.
            request           Send a request message to some service and output the reply.
            inspect           Describe the available rpc methods of a service.
            discover          Show available services.
            help              Display help information about iris.
            list              List available commands.
            subscribe         Prints events to stdout.
            instance          Run a single service instance (one process).
            node              Run a node service that manages a group of processes on the same machine.
        """, config=False)


class HelpCommandTests(CliTestMixin, unittest.TestCase):
    def test_help(self):
        self.assert_first_line_equals(['help'], 'Usage: iris [options] <command> [<args>...]', config=False)

    def test_help_list(self):
        self.assert_first_line_equals(['help', 'list'], 'Usage: iris list [options]', config=False)


class ServiceCommandTests(CliIntegrationTestCase):
    def test_instance(self):
        self.cli_config['interfaces'] = {
            'echo': {
                'class': 'iris.tests.integration.test_cli:Upper',
            }
        }
        self.cli_config['registry']['hosts'] = self.hosts
        command_greenlet = gevent.spawn(self.cli, ['instance'])
        client = self.create_client()
        gevent.sleep(1)  # FIXME: how can we wait for the instance to register?
        response = client.request('iris://upper', 'upper.upper', {'text': 'hi'}, timeout=1)
        self.assertEqual(response.body, 'HI')
        command_greenlet.kill()
        command_greenlet.join()
