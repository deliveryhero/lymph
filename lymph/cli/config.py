from __future__ import print_function
import yaml
from lymph.cli.base import Command

import zmq.green.core


class ConfigCommand(Command):
    """
    Usage: lymph config [options]

    Prints configuration for inspection

    {COMMON_OPTIONS}
    """

    short_description = 'Prints configuration for inspection'

    @staticmethod
    def socket_representer(dumper, socket):
        return dumper.represent_scalar('!socket', '...', style=None)

    def run(self):
        yaml.add_representer(zmq.green.core._Socket, self.socket_representer)
        print(yaml.dump(self.config.values))
