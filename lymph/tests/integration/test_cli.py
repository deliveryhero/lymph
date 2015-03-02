import unittest
import gevent


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

    def tearDown(self):
        self.upper_container.stop()
        self.upper_container.join()
        super(RequestCommandTests, self).tearDown()

    def test_request(self):
        result = self.cli(['request', 'upper.upper', '{"text":"foo"}'])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, 'FOO\n')

    def test_negative_request(self):
        result = self.cli(['request', 'no_exiting_container', '{}'])
        self.assertEqual(result.returncode, 1)

    def test_inspect(self):
        # Use --no-color to facilitate string comparison.
        result = self.cli(['inspect', '--no-color', 'upper'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('rpc upper.upper(text)', result.stdout)

    def test_negative_inspect(self):
        result = self.cli(['inspect', 'no_existing_container'])
        self.assertEqual(result.returncode, 1)


class ListCommandTests(CliTestMixin, unittest.TestCase):
    def test_list(self):
        self.assert_lines_equal(['list'], """
            tail              Stream the logs of one or more services.
            emit              Manually emits an event.
            request           Send a request message to some service and output the reply.
            inspect           Describe the available rpc methods of a service.
            discover          Show available services.
            help              Display help information about lymph.
            list              List available commands.
            subscribe         Prints events to stdout.
            instance          Run a single service instance (one process).
            node              Run a node service that manages a group of processes on the same machine.
            shell             Open an interactive Python shell locally or remotely.
        """, config=False)


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
        self.cli_config['registry']['hosts'] = self.hosts
        command_greenlet = gevent.spawn(self.cli, ['instance'])
        client = self.create_client()
        gevent.sleep(1)  # FIXME: how can we wait for the instance to register?
        response = client.request('echo', 'echo.upper', {'text': 'hi'}, timeout=1)
        self.assertEqual(response.body, 'HI')
        command_greenlet.kill()
        command_greenlet.join()
