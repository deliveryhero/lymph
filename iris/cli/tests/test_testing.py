import unittest

from iris.cli import base
from iris.cli.testing import CommandFactory


class CommandFactoryTest(unittest.TestCase):

    def test_returns_a_command_instance(self):
        class ExampleCommand(base.Command):
            def run(self):
                pass

        _create_command = CommandFactory(ExampleCommand)
        cmd = _create_command()
        self.assertIsInstance(cmd, ExampleCommand)
