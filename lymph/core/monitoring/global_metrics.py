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


class GlobalMetrics(object):
    def __call__(self):
        return iter(self)


class RUsageMetrics(GlobalMetrics):
    def __init__(self, name='rusage'):
        self.attr_map = [('ru_{}'.format(attr), '{}.{}'.format(name, attr)) for attr in RUSAGE_ATTRS]

    def __iter__(self):
        ru = resource.getrusage(resource.RUSAGE_SELF)
        for ru_attr, series_name in self.attr_map:
            yield metrics.RawMetric(series_name, getattr(ru, ru_attr))


class GarbageCollectionMetrics(GlobalMetrics):
    def __init__(self, name='gc'):
        self.name = name

    def __iter__(self):
        yield metrics.RawMetric('{}.garbage'.format(self.name), len(gc.garbage))
        for i, count in enumerate(gc.get_count()):
            yield metrics.RawMetric('{}.count{}'.format(self.name, i), count)


class GeventMetrics(GlobalMetrics):
    def __init__(self, name='gevent'):
        self.name = name

    def __iter__(self):
        hub = gevent.get_hub()
        threadpool, loop = hub.threadpool, hub.loop
        yield metrics.RawMetric('gevent.threadpool.size', threadpool.size)
        yield metrics.RawMetric('gevent.threadpool.maxsize', threadpool.maxsize)
        yield metrics.RawMetric('gevent.active', loop.activecnt)
        yield metrics.RawMetric('gevent.pending', loop.pendingcnt)
        yield metrics.RawMetric('gevent.depth', loop.depth)
