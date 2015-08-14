import lymph
from lymph.client import Client
from lymph.cli.base import Command


class SubscribeCommand(Command):
    """
    Usage: lymph subscribe <event-type>... [options]

    Subscribes to event types and prints occurences on stdout

    {COMMON_OPTIONS}
    """

    short_description = 'Subscribes to event types and prints occurences on stdout'

    def run(self):
        event_type = self.args.get('<event-type>')

        class Subscriber(lymph.Interface):
            @lymph.event(*event_type)
            def on_event(self, event):
                print('%s: %r' % (event.evt_type, event.body))

        client = Client.from_config(self.config, interface_cls=Subscriber)
        client.container.join()

