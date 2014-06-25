from contextlib import contextmanager
import sys
import os
import tempfile
import textwrap

from pkg_resources import load_entry_point
from six import StringIO
import yaml

from lymph.discovery.zookeeper import ZookeeperServiceRegistry
from lymph.events.null import NullEventSystem
from lymph.testing import LymphIntegrationTestCase


@contextmanager
def capture_stdout():
    real_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        yield sys.stdout
    finally:
        sys.stdout = real_stdout


class CliWrapper(object):
    def __init__(self, config):
        handle, self.config_file_name = tempfile.mkstemp()
        with open(self.config_file_name, 'w') as f:
            f.write(yaml.dump(config))
        self.entry_point = load_entry_point('lymph', 'console_scripts', 'lymph')

    def tear_down(self):
        os.remove(self.config_file_name)

    def __call__(self, cmd, config=True):
        with capture_stdout() as stdout:
            if config:
                cmd = cmd + ['--config=%s' % self.config_file_name]
            try:
                self.entry_point(cmd)
            except SystemExit:
                # Docopt tries to exit on its own unfortunately
                pass
            return stdout.getvalue()


class CliTestMixin(object):

    cli_config = {}

    _help_output = None

    @property
    def cli(self):
        if not hasattr(self, '_cli'):
            self._cli = CliWrapper(self.cli_config)
        return self._cli

    def tearDown(self):
        if hasattr(self, '_cli'):
            self._cli.tear_down()
        super(CliTestMixin, self).tearDown()

    def assert_lines_equal(self, cmd, lines, config=True):
        expected_lines = set(line for line in textwrap.dedent(lines).splitlines() if line.strip())
        self.assertEqual(set(self.cli(cmd, config=config).splitlines()), expected_lines)

    def assert_first_line_equals(self, cmd, line, config=True):
        self.assertEqual(self.cli(cmd, config=config).splitlines()[0].strip(), line)

    def assert_command_appears_in_command_list(self):
        output = self.cli(['list'])
        self.assertIn(self.command_name, output)

    def assert_help_contains_usage_information(self):
        output = self._get_help_output()
        self.assertIn('Usage', output)
        self.assertIn(self.command_name, output)

    def assert_help_contains_parameter(self, parameter, default=None):
        self.assert_help_contains(parameter)
        if default is not None:
            self.assert_help_contains(default)

    def assert_help_contains(self, text):
        self.assertIn(text, self._get_help_output())

    def _get_help_output(self):
        if self._help_output is None:
            output = self.cli([self.command_name, '--help'])
            self._help_output = output
        return self._help_output


class CliIntegrationTestCase(CliTestMixin, LymphIntegrationTestCase):
    use_zookeeper = True

    def setUp(self):
        super(CliIntegrationTestCase, self).setUp()
        self.registry = ZookeeperServiceRegistry(self.hosts)
        self.events = NullEventSystem()

        self.cli_config = {
            "registry": {
                "class": "lymph.discovery.zookeeper:ZookeeperServiceRegistry",
                "hosts": self.hosts,
            },
            "event_system": {
                "class": "lymph.events.null:NullEventSystem",
            },
        }


class CommandFactory(object):
    """
    Encapsulates the knowledge how to create a command instance.

    Intended use is to support smaller unit tests which just need an instance
    of a command class to try out some method.

    It only supports to pass in parameters as keyword parameters into
    the command constructor.
    """

    def __init__(self, command_class):
        self.command_class = command_class

    def __call__(self, **kwargs):
        kwargs.setdefault('args', {})
        kwargs.setdefault('config', {})
        kwargs.setdefault('terminal', None)
        return self.command_class(**kwargs)
