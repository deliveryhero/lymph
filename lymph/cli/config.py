from __future__ import print_function
import yaml
from lymph.cli.base import Command


class ConfigCommand(Command):
    """
    Usage: lymph config [options]

    Outputs the configuration.

    {COMMON_OPTIONS}
    """
    
    short_description = 'Show configuration.'

    def run(self):
        print(yaml.safe_dump(self.config.values))
