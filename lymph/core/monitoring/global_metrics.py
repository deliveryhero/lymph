import gc

import resource
import gevent

from . import metrics


RUSAGE_ATTRS = (
    'utime', 'stime',
    'maxrss', 'ixrss', 'idrss', 'isrss',
    'minflt', 'majflt', 'nswap',
    'inblock', 'oublock',
    'msgsnd', 'msgrcv',
    'nsignals', 'nvcsw', 'nivcsw',
)


class RUsageMetrics(object):
    def __init__(self, name='rusage'):
        self.attr_map = [('ru_{}'.format(attr), '{}.{}'.format(name, attr)) for attr in RUSAGE_ATTRS]

    def __iter__(self):
        ru = resource.getrusage(resource.RUSAGE_SELF)
        for ru_attr, series_name in self.attr_map:
            yield series_name, getattr(ru, ru_attr), {}


class GarbageCollectionMetrics(object):
    def __init__(self, name='gc'):
        self.name = name

    def __iter__(self):
        yield '{}.garbage'.format(self.name), len(gc.garbage), {}
        for i, count in enumerate(gc.get_count()):
            yield '{}.count{}'.format(self.name, i), count, {}


class GeventMetrics(object):
    def __init__(self, name='gevent'):
        self.name = name

    def __iter__(self):
        hub = gevent.get_hub()
        threadpool, loop = hub.threadpool, hub.loop
        yield 'gevent.threadpool.size', threadpool.size, {}
        yield 'gevent.threadpool.maxsize', threadpool.maxsize, {}
        yield 'gevent.active', loop.activecnt, {}
        yield 'gevent.pending', loop.pendingcnt, {}
        yield 'gevent.depth', loop.depth, {}
