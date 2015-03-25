import logging
import time

import gevent
import msgpack
import zmq.green as zmq

from lymph.core.components import Component
from lymph.core.monitoring.metrics import Metrics
from lymph.core.monitoring.global_metrics import RUsageMetrics, GeventMetrics, GarbageCollectionMetrics


logger = logging.getLogger(__name__)


DEFAULT_MONITOR_ENDPOINT = 'tcp://127.0.0.1:44044'


class MonitorPusher(Component):
    def __init__(self, container, endpoint=None, interval=2):
        super(MonitorPusher, self).__init__()
        self.container = container
        self.interval = interval
        self.endpoint = endpoint or DEFAULT_MONITOR_ENDPOINT
        logger.info('connecting to monitor endpoint %s', self.endpoint)
        ctx = zmq.Context.instance()
        self.socket = ctx.socket(zmq.PUB)
        self.socket.connect(self.endpoint)

        self.aggregate = Metrics()
        self.aggregate.add(RUsageMetrics())
        self.aggregate.add(GarbageCollectionMetrics())
        self.aggregate.add(GeventMetrics())
        self.aggregate.add(container.metrics)

    def add_tags(self, **tags):
        self.aggregate.add_tags(**tags)

    def on_start(self):
        self.loop_greenlet = self.container.spawn(self.loop)

    def on_stop(self, **kwargs):
        self.loop_greenlet.kill()

    def loop(self):
        last_stats = time.monotonic()
        while True:
            gevent.sleep(self.interval)
            dt = time.monotonic() - last_stats
            series = list(self.aggregate)
            stats = {
                'time': time.time(),
                'series': series,
            }
            last_stats += dt
            self.socket.send_multipart([b'stats', msgpack.dumps(stats)])
