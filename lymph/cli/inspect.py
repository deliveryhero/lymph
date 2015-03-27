import textwrap

from lymph.client import Client
from lymph.cli.base import Command, handle_request_errors


class InspectCommand(Command):
    """
    Usage: lymph inspect [--ip=<address> | --guess-external-ip | -g] <address> [options]

    Options:
      --ip=<address>               Use this IP for all sockets.
      --guess-external-ip, -g      Guess the public facing IP of this machine and
                                   use it instead of the provided address.

    {COMMON_OPTIONS}

    """

    short_description = 'Describe the available rpc methods of a service.'

    @handle_request_errors
    def run(self):
        client = Client.from_config(self.config)
        result = client.request(self.args['<address>'], 'lymph.inspect', {}, timeout=5).body
        print()

        for method in sorted(result['methods'], key=lambda m: m['name']):
            print("rpc {name}({params})\n    {help}\n".format(
                name=self.terminal.red(method['name']),
                params=', '.join(method['params']),
                help='\n    '.join(textwrap.wrap(method['help'], 70)),
            ))

