import logging
import uuid

import gevent

from lymph.utils.gpool import NonBlockingPool


logger = logging.getLogger(__name__)


def get_trace(greenlet=None):
    greenlet = greenlet or gevent.getcurrent()
    if not hasattr(greenlet, '_lymph_trace'):
        greenlet._lymph_trace = {}
    return greenlet._lymph_trace


class GreenletWithTrace(gevent.Greenlet):
    def __init__(self, *args, **kwargs):
        super(GreenletWithTrace, self).__init__(*args, **kwargs)
        self._lymph_trace = get_trace().copy()


class Group(NonBlockingPool):
    greenlet_class = GreenletWithTrace


def trace(**kwargs):
    get_trace().update(kwargs)


def set_id(trace_id=None):
    tid = trace_id or uuid.uuid4().hex
    trace(lymph_trace_id=tid)
    if trace_id is None:
        logger.debug('starting trace')
    return tid


def get_id():
    return get_trace().get('lymph_trace_id')


class TraceFormatter(logging.Formatter):
    def format(self, record):
        record.trace_id = get_id()
        return super(TraceFormatter, self).format(record)
