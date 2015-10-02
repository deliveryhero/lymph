import hashlib
import logging
import collections

import lymph
import gevent
from kazoo.handlers.gevent import SequentialGeventHandler

from lymph.core.declarations import Declaration
from lymph.core.events import Event
from lymph.core.interfaces import Component


logger = logging.getLogger(__name__)


def serial_event(*event_types, **kwargs):
    if 'key' not in kwargs:
        raise TypeError('key argument is required')

    def decorator(func):
        def factory(interface):
            zkclient = interface.config.root.get_instance(
                'components.SerialEventHandler.zkclient',
                handler=SequentialGeventHandler())
            return SerialEventHandler(zkclient, interface, func, event_types, **kwargs)
        return Declaration(factory)
    return decorator


class SerialEventHandler(Component):
    def __init__(self, zkclient, interface, func, event_types, key, partition_count=12):
        super(SerialEventHandler, self).__init__()
        self.zk = zkclient
        self.interface = interface
        self.partition_count = partition_count
        self.key = key
        self.consumer_func = func
        self.consumers = collections.OrderedDict()
        self.name = '%s.%s' % (interface.name, func.__name__)

        def _consume(interface, event):
            self.consumer_func(self.interface, Event.deserialize(event['event']))

        for i in range(partition_count):
            queue = self.get_queue_name(i)
            e = lymph.event(queue, queue_name=queue, sequential=True, active=False)(_consume)
            handler = interface.install(e)
            self.consumers[handler] = interface.container.subscribe(handler, consume=False)
        self.partition = set()
        push_queue = self.get_queue_name('push')
        interface.install(lymph.event(*event_types, queue_name=push_queue)(self.push))

    def on_start(self):
        super(SerialEventHandler, self).on_start()
        self.start()

    def on_stop(self, **kwargs):
        super(SerialEventHandler, self).on_stop(**kwargs)
        self.running = False

    def get_queue_name(self, index):
        return '%s.%s' % (self.consumer_func.__name__, index)

    def push(self, interface, event):
        key = str(self.key(interface, event)).encode('utf-8')
        index = int(hashlib.md5(key).hexdigest(), 16) % self.partition_count
        logger.debug('PUBLISH %s %s', self.get_queue_name(index), event)
        self.interface.emit(self.get_queue_name(index), {'event': event.serialize()})

    def start(self):
        self.running = True
        self.interface.container.spawn(self.loop)

    def loop(self):
        while self.running:
            logger.info('starting partitioner')
            partitioner = self.zk.SetPartitioner(
                path='/lymph/serial_event_partitions/%s' % self.name,
                set=self.consumers.keys(),
                time_boundary=1,
            )
            while True:
                if partitioner.failed:
                    logger.error('partitioning failed')
                    break
                elif partitioner.release:
                    self.release_partition()
                    partitioner.release_set()
                elif partitioner.acquired:
                    self.update_partition(set(partitioner))
                    gevent.sleep(1)
                elif partitioner.allocating:
                    partitioner.wait_for_acquire()

    def release_partition(self):
        for handler in self.partition:
            self.stop_consuming(handler)
        self.partition = set()

    def update_partition(self, partition):
        for queue in self.partition - partition:
            self.stop_consuming(queue)
        for queue in partition - self.partition:
            self.start_consuming(queue)
        if partition != self.partition:
            logger.info('partition: %s', ', '.join(h.queue_name for h in partition))
        self.partition = partition

    def start_consuming(self, handler):
        self.consumers[handler].start()

    def stop_consuming(self, handler):
        self.consumers[handler].stop()
