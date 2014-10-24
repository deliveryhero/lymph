import logging
import collections

import six
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

    def _connect(self, instance):
        """Connect to a given service instance."""
        self._sock.connect(instance.log_endpoint)
        self._instances[instance.log_endpoint] = instance

    def _disconnect(self, instance):
        """Disconnect from a service instance."""
        self._sock.disconnect(instance.log_endpoint)
        del self._instances[instance.log_endpoint]

    def subscribe_service(self, service):
        """Subscribe to a service stream.

        This is done by iterating over all instances in this service and
        connecting to them, while keeping tabs over this service to be able
        to connect and disconnect as instances get added or removed.

        """
        # FIXME(mouad): Make sure that service implement the Observable
        # interface bug: GUP-126
        service.observe(services.ADDED, self._connect)
        service.observe(services.REMOVED, self._disconnect)

        for instance in service:
            if instance.log_endpoint:
                self._connect(instance)

    def next(self):
        """Return an instance of :class:`RemoteTail.Entry`."""
        topic, endpoint, msg = self._sock.recv_multipart()
        return self.Entry(topic, self._instances[endpoint], msg)

    __next__ = next  # For python3.


class TailCommand(Command):
    """
    Usage: lymph tail [options] [--level=<level> | -l <level>] <address>...

    Description:
        Shows the log output of <address>

    Tail Options:
      --level=<level>, -l <level>  Log level to subscribe to [default: INFO]

    {COMMON_OPTIONS}
    """

    short_description = 'Stream the logs of one or more services.'

    def run(self):
        client = Client.from_config(self.config)
        tail = RemoteTail()

        for address in self.args['<address>']:
            tail.subscribe_service(client.container.lookup(address))

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
