import logging
import six
import zmq.green as zmq

from iris.cli.base import Command
from iris.client import Client
from iris.utils.logging import get_loglevel


class TailCommand(Command):
    """
    Usage: iris tail [options] [--level=<level> | -l <level>] <address>...

    Description:
        Shows the log output of <address>

    Tail Options:
      --level=<level>, -l <level>  Log level to subscribe to [default: INFO]

    {COMMON_OPTIONS}
    """

    short_description = 'Stream the logs of one or more services.'

    def run(self):
        client = Client.from_config(self.config)
        instances = {}
        for address in self.args['<address>']:
            service = client.container.lookup(address)
            for instance in service:
                if instance.log_endpoint:
                    instances[instance.log_endpoint] = instance, address

        ctx = zmq.Context.instance()
        sock = ctx.socket(zmq.SUB)
        sock.setsockopt_string(zmq.SUBSCRIBE, u'')
        for instance, service_type in six.itervalues(instances):
            sock.connect(instance.log_endpoint)

        level = get_loglevel(self.args['--level'])
        logger = logging.getLogger('iris-tail-cli')
        logger.setLevel(level)
        console = logging.StreamHandler()
        console.setLevel(level)
        console.setFormatter(logging.Formatter('[%(service_type)s][%(identity)s] [%(levelname)s] %(message)s'))
        logger.addHandler(console)
        try:
            while True:
                topic, endpoint, msg = sock.recv_multipart()
                level = getattr(logging, topic)
                instance, service_type = instances[endpoint]
                logger.log(level, msg, extra={
                    'identity': instance.identity[:10],
                    'service_type': service_type,
                })
        except KeyboardInterrupt:
            pass
