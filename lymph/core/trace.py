import gevent
import gevent.pool
import uuid
import logging


logger = logging.getLogger(__name__)


def get_trace(greenlet=None):
    greenlet = greenlet or gevent.getcurrent()
    if not hasattr(greenlet, '_lymph_trace'):
        greenlet._lymph_trace = {}
    return greenlet._lymph_trace


def spawn(*args, **kwargs):
    greenlet = gevent.Greenlet(*args, **kwargs)
    greenlet._lymph_trace = get_trace().copy()
    greenlet.start()
    return greenlet


_spawn = spawn

class Group(gevent.pool.Group):
    def spawn(self, *args, **kwargs):
        g = _spawn(*args, **kwargs)
        self.add(g)
        return g


def trace(**kwargs):
    get_trace().update(kwargs)


def set_id(trace_id=None):
    tid = trace_id or uuid.uuid4().hex
    trace(lymph_trace_id=tid)
    if trace_id is None:
        logger.info('starting trace')
    return tid


def get_id():
    return get_trace().get('lymph_trace_id')


class TraceFormatter(logging.Formatter):
    def format(self, record):
        record.trace_id = get_id()
        return super(TraceFormatter, self).format(record)
