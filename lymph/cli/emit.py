import json

from lymph.client import Client
from lymph.cli.base import Command


class EmitCommand(Command):
    """
    Usage: lymph emit <event-type> [<body>] [options]

    {COMMON_OPTIONS}
    """

    short_description = 'Manually emits an event.'

    def run(self):
        event_type = self.args.get('<event-type>')
        body = json.loads(self.args.get('<body>'))

        client = Client.from_config(self.config)
        client.emit(event_type, body)

