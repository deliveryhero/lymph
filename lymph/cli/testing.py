import collections
from contextlib import contextmanager
import sys
import os
import tempfile
import textwrap

from kazoo.client import KazooClient
from kazoo.handlers.gevent import SequentialGeventHandler
from pkg_resources import load_entry_point
from six import StringIO, integer_types
import yaml

from lymph.discovery.zookeeper import ZookeeperServiceRegistry
from lymph.events.null import NullEventSystem
from lymph.testing import LymphIntegrationTestCase


@contextmanager
def capture_output():
    real_stdout = sys.stdout
    real_stderr = sys.stderr
    sys.stdout = StringIO()
    sys.stderr = StringIO()
    try:
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout = real_stdout
        sys.stderr = real_stderr


class CliWrapper(object):

    Result = collections.namedtuple('CMDLineResult', 'returncode stdout stderr')

    def __init__(self, config):
        handle, self.config_file_name = tempfile.mkstemp()
        with open(self.config_file_name, 'w') as f:
            f.write(yaml.dump(config))
        self.entry_point = load_entry_point('lymph', 'console_scripts', 'lymph')

    def tear_down(self):
        os.remove(self.config_file_name)

    def __call__(self, cmd, config=True):
        with capture_output() as (stdout, stderr):
            if config:
                cmd = cmd + ['--config=%s' % self.config_file_name]
            try:
                returncode = self.entry_point(cmd)
            except SystemExit as ex:
                # Docopt tries to exit on its own unfortunately
                returncode = (ex.args[0] or 0) if ex.args else 0
                if not isinstance(returncode, integer_types):
                    # According to sys.exit doc, any other object beside
                    # an integer or None result to an exit code equal to 1.
                    returncode = 1
            return self.Result(
                returncode or 0, stdout.getvalue(), stderr.getvalue())


class CliTestMixin(object):

    cli_config = {}

    _help_output = None

    def setUp(self):
        self.__clis = []
        super(CliTestMixin, self).setUp()

    @property
    def cli(self):
        cli = CliWrapper(self.cli_config)
        self.__clis.append(cli)
        return cli

    def tearDown(self):
        for cli in self.__clis:
            cli.tear_down()
        super(CliTestMixin, self).tearDown()

    def assert_lines_equal(self, cmd, lines, config=True):
        expected_lines = set(line for line in textwrap.dedent(lines).splitlines() if line.strip())
        result = self.cli(cmd, config=config)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(set(result.stdout.splitlines()), expected_lines)

    def assert_first_line_equals(self, cmd, line, config=True):
        result = self.cli(cmd, config=config)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.splitlines()[0].strip(), line)

    def assert_command_appears_in_command_list(self):
        result = self.cli(['list'])
        self.assertEqual(result.returncode, 0)
        self.assertIn(self.command_name, result.stdout)

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
            result = self.cli([self.command_name, '--help'])
            self._help_output = result.stdout
        return self._help_output


class CliIntegrationTestCase(CliTestMixin, LymphIntegrationTestCase):
    use_zookeeper = True

    def setUp(self):
        super(CliIntegrationTestCase, self).setUp()
        client = KazooClient(
            hosts=self.hosts,
            handler=SequentialGeventHandler(),
        )
        self.registry = ZookeeperServiceRegistry(client)
        self.events = NullEventSystem()

        self.cli_config = {
            "container": {
                "registry": {
                    "class": "lymph.discovery.zookeeper:ZookeeperServiceRegistry",
                    "zkclient": 'dep:kazoo',
                },
                "events": {
                    "class": "lymph.events.null:NullEventSystem",
                },
            },
            "dependencies": {
                "kazoo": {
                    "class": "kazoo.client:KazooClient",
                    "hosts": self.hosts,
                }
            }
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
