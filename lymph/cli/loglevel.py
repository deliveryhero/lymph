# -*- coding: utf-8 -*-
from __future__ import print_function

from lymph.client import Client
from lymph.cli.base import Command, handle_request_errors


class LogLevelCommand(Command):
    """
    Usage: lymph change-loglevel <address> [options]

    Sets the log level of a service's logger (all instances) for a given amount of time and then resets.

    Options:
      --name=<name>, -n            Logger name to change.
      --level=<level>, -l          Logging level to use.
      --period=<seconds>, -p       Period where change will be effected, after
                                   the logging level will be reverted [default: 60]
      --guess-external-ip, -g      Guess the public facing IP of this machine and
                                   use it instead of the provided address.

    {COMMON_OPTIONS}
    """

    short_description = 'Set logging level of a service logger'

    @handle_request_errors
    def run(self):
        try:
            period = float(self.args.get('--period'))
        except ValueError:
            print("--period requires a number (e.g. --period=0.42)")
            return 1

        return self.change_loglevel(
            address=self.args['<address>'],
            logger=self.args['--name'],
            level=self.args['--level'],
            period=period,
        )

    def change_loglevel(self, address, logger, level, period):
        client = Client.from_config(self.config)
        body = {
            'qualname': logger,
            'loglevel': level,
            'period': period,
        }
        service = client.container.lookup(address)
        print("Changing logger '%s' of '%s' to '%s' for a period of %s seconds" %
              (logger, address, level, period))
        for instance in service:
            client.request(instance.endpoint, 'lymph.change_loglevel', body)

