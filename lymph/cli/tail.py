from __future__ import print_function

import logging
import collections

import zmq.green as zmq

from lymph.cli.base import Command
from lymph.client import Client
from lymph.core import services
from lymph.utils.logging import get_loglevel


class RemoteTail(collections.Iterator):
    """Tail remotely a stream of services published messages.

    Instance of this class implement the iterator protocol, which return
    messages as published by the remote services that this instance is register
    to.

    """

    Entry = collections.namedtuple('Entry', 'topic instance msg')

    def __init__(self, ctx=None):
        if ctx is None:
            ctx = zmq.Context.instance()

        self._sock = ctx.socket(zmq.SUB)
        self._sock.setsockopt_string(zmq.SUBSCRIBE, u'')
        self._instances = {}

    @property
    def instances(self):
        return self._instances

    def _on_status_change(self, instance, action):
        """Connect to a given service instance."""
        if action == services.ADDED:
            self._connect(instance)
        elif action == services.REMOVED:
            self._disconnect(instance)

    def _connect(self, instance):
        self._sock.connect(instance.log_endpoint)
        self._instances[instance.log_endpoint] = instance

    def _disconnect(self, instance):
        self._sock.disconnect(instance.log_endpoint)
        del self._instances[instance.log_endpoint]

    def subscribe_service(self, service):
        """Subscribe to a service stream.

        This is done by iterating over all instances in this service and
        connecting to them, while keeping tabs over this service to be able
        to connect and disconnect as instances get added or removed.

        Return: True if subscription worked else false.

        """
        service.observe([services.ADDED, services.REMOVED], self._on_status_change)

        connected = False
        for instance in service:
            if instance.log_endpoint:
                self._connect(instance)
                connected = True
        return connected

    def next(self):
        """Return an instance of :class:`RemoteTail.Entry`."""
        topic, endpoint, msg = self._sock.recv_multipart()
        return self.Entry(topic, self._instances[endpoint], msg)

    __next__ = next  # For python3.


class TailCommand(Command):
    """
    Usage: lymph tail [options] [--level=<level> | -l <level>] <address>...

    Streams the log output of services to stderr

    Options:
      --level=<level>, -l <level>  Log level to subscribe to [default: INFO]

    {COMMON_OPTIONS}
    """

    short_description = 'Streams the log output of services to stderr'

    def run(self):
        client = Client.from_config(self.config)
        tail = RemoteTail()

        for address in self.args['<address>']:
            connected = tail.subscribe_service(client.container.lookup(address))
            if not connected:
                print("Couldn't connect to log endpoint of '%s'" % address)

        if not tail.instances:
            return 1

        level = get_loglevel(self.args['--level'])
        logger = logging.getLogger('lymph-tail-cli')
        logger.setLevel(level)

        console = logging.StreamHandler()
        console.setLevel(level)
        console.setFormatter(logging.Formatter('[%(service_type)s][%(identity)s] [%(levelname)s] %(message)s'))

        logger.addHandler(console)

        try:
            for topic, instance, msg in tail:
                level = getattr(logging, topic)
                extra = {
                    'identity': instance.identity[:10],
                    'service_type': instance.endpoint,
                }
                logger.log(level, msg, extra=extra)
        except KeyboardInterrupt:
            pass
