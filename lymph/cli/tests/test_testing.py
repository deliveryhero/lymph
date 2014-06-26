import unittest

from lymph.cli import base
from lymph.cli.testing import CommandFactory


class CommandFactoryTest(unittest.TestCase):

    def test_returns_a_command_instance(self):
        class ExampleCommand(base.Command):
            def run(self):
                pass

        _create_command = CommandFactory(ExampleCommand)
        cmd = _create_command()
        self.assertIsInstance(cmd, ExampleCommand)
