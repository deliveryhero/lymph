import json

from lymph.client import Client
from lymph.cli.base import Command
from lymph.core import trace


class EmitCommand(Command):
    """
    Usage: lymph emit <event-type> [<body>] [options]

    Options:
      --trace-id=<trace_id>        Use the given trace_id.

    {COMMON_OPTIONS}
    """

    short_description = 'Manually emits an event.'

    def run(self):
        event_type = self.args.get('<event-type>')
        body = json.loads(self.args.get('<body>'))

        trace.set_id(self.args.get('--trace-id'))
        client = Client.from_config(self.config)
        client.emit(event_type, body)
