import logging
import time

import gevent
import msgpack
import zmq.green as zmq

from lymph.core.components import Component
from lymph.utils.sockets import bind_zmq_socket


logger = logging.getLogger(__name__)


class MonitorPusher(Component):
    def __init__(self, container, aggregator, endpoint='127.0.0.1', interval=2):
        super(MonitorPusher, self).__init__()
        self.container = container
        self.interval = interval
        ctx = zmq.Context.instance()
        self.socket = ctx.socket(zmq.PUB)
        self.endpoint, port = bind_zmq_socket(self.socket, endpoint)
        logger.info('binding monitoring endpoint %s', self.endpoint)
        self.aggregator = aggregator

    def on_start(self):
        self.loop_greenlet = self.container.spawn(self.loop)

    def on_stop(self, **kwargs):
        self.loop_greenlet.kill()

    def loop(self):
        last_stats = time.monotonic()
        while True:
            gevent.sleep(self.interval)
            dt = time.monotonic() - last_stats
            series = list(self.aggregator.get_metrics())
            stats = {
                'time': time.time(),
                'series': series,
            }
            last_stats += dt
            self.socket.send_multipart([b'stats', msgpack.dumps(stats)])
