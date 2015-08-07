import gc
import resource

import gevent
import psutil


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


class ProcessMetrics(object):
    def __init__(self):
        self.proc = psutil.Process()

    def __iter__(self):
        meminfo = self.proc.memory_info()._asdict()
        yield 'proc.mem.rss', meminfo['rss'], {}
        yield 'proc.mem.vms', meminfo['vms'], {}

        # Not available in OSX and solaris.
        if hasattr(self.proc, 'io_counters'):
            io_counts = self.proc.io_counters()
            yield 'proc.io.read_count', io_counts.read_count, {}
            yield 'proc.io.write_count', io_counts.write_count, {}
            yield 'proc.io.read_bytes', io_counts.read_bytes, {}
            yield 'proc.io.write_bytes', io_counts.write_bytes, {}

        ctxt_switches = self.proc.num_ctx_switches()
        yield 'proc.ctxt_switches.voluntary', ctxt_switches.voluntary, {}
        yield 'proc.ctxt_switches.involuntary', ctxt_switches.involuntary, {}

        cpu_times = self.proc.cpu_times()
        yield 'proc.cpu.user', cpu_times.user, {}
        yield 'proc.cpu.system', cpu_times.system, {}

        soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
        yield 'proc.files.count', self.proc.num_fds(), {}
        yield 'proc.files.soft_limit', soft_limit, {}
        yield 'proc.files.hard_limit', hard_limit, {}

        yield 'proc.threads.count', self.proc.num_threads(), {}

        yield 'proc.sockets.count', len(self.proc.connections()), {}
