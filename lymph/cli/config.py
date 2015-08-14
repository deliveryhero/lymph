from __future__ import print_function
import yaml
from lymph.cli.base import Command


class ConfigCommand(Command):
    """
    Usage: lymph config [options]

    Prints configuration for inspection

    {COMMON_OPTIONS}
    """
    
    short_description = 'Prints configuration for inspection'

    def run(self):
        print(yaml.safe_dump(self.config.values))
