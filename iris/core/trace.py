import gevent
import gevent.pool
import uuid
import logging


def get_trace(greenlet=None):
    greenlet = greenlet or gevent.getcurrent()
    if not hasattr(greenlet, '_iris_trace'):
        greenlet._iris_trace = {}
    return greenlet._iris_trace


def spawn(*args, **kwargs):
    greenlet = gevent.Greenlet(*args, **kwargs)
    greenlet._iris_trace = get_trace().copy()
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
    trace_id = trace_id or uuid.uuid4().hex
    trace(iris_trace_id=trace_id)
    return trace_id


def get_id():
    return get_trace().get('iris_trace_id')


class TraceFormatter(logging.Formatter):
    def format(self, record):
        record.trace_id = get_id()
        return super(TraceFormatter, self).format(record)
