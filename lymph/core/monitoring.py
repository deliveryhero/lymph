import gevent
import logging
import msgpack
import resource
import time
import zmq.green as zmq


logger = logging.getLogger(__name__)


RUSAGE_ATTRS = (
    'utime', 'stime',
    'maxrss', 'ixrss', 'idrss', 'isrss',
    'minflt', 'majflt', 'nswap',
    'inblock', 'oublock',
    'msgsnd', 'msgrcv',
    'nsignals', 'nvcsw', 'nivcsw',
)

DEFAULT_MONITOR_ENDPOINT = 'tcp://127.0.0.1:44044'


class Monitor(object):
    def __init__(self, container, endpoint=None):
        self.container = container
        self.stats = None
        self.endpoint = endpoint or DEFAULT_MONITOR_ENDPOINT
        logger.info('connecting to monitor endpoint %s', self.endpoint)
        ctx = zmq.Context.instance()
        self.socket = ctx.socket(zmq.PUB)
        self.socket.connect(self.endpoint)

    def start(self):
        self.loop_greenlet = self.container.spawn(self.loop)

    def stop(self):
        self.loop_greenlet.kill()

    def get_rusage_stats(self, ru, previous):
        stats = {}
        for attr in RUSAGE_ATTRS:
            ru_attr = 'ru_%s' % attr
            stats[attr] = getattr(ru, ru_attr) - getattr(previous, ru_attr)
        return stats

    def loop(self):
        last_stats = time.monotonic()
        last_rusage = resource.getrusage(resource.RUSAGE_SELF)
        while True:
            gevent.sleep(2)
            dt = time.monotonic() - last_stats
            self.stats = self.container.stats()
            ru = resource.getrusage(resource.RUSAGE_SELF)
            self.stats.update({
                'dt': dt,
                'time': time.time(),
                'rusage': self.get_rusage_stats(ru, last_rusage),
            })
            last_rusage = ru
            last_stats += dt
            self.socket.send_multipart([
                b'stats',
                msgpack.dumps(self.stats)])
