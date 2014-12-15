from __future__ import absolute_import

from contextlib import contextmanager

import logging
import gevent
import gevent.pool
import kombu
import kombu.mixins
import kombu.pools

from lymph.events.base import BaseEventSystem
from lymph.core.events import Event


logger = logging.getLogger(__name__)


DEFAULT_SERIALIZER = 'lymph-msgpack'
DEFAULT_EXCHANGE = 'lymph'


class EventConsumer(kombu.mixins.ConsumerMixin):
    def __init__(self, connection, queue, handler, spawn=gevent.spawn):
        self.connection = connection
        self.queue = queue
        self.handler = handler
        self.spawn = spawn
        self.greenlet = None

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=[self.queue], callbacks=[self.on_kombu_message])]

    def create_connection(self):
        return kombu.pools.connections[self.connection].acquire(block=True)

    def on_kombu_message(self, body, message):
        logger.debug("received kombu message %r", body)

        def message_handler():
            try:
                event = Event.deserialize(body)
                self.handler(event)
                message.ack()
            except:
                logger.exception('failed to handle event from queue %r', self.handler.queue_name)

        if self.handler.sequential:
            message_handler()
        else:
            self.spawn(message_handler)

    def start(self):
        if self.greenlet:
            return
        self.should_stop = False
        self.greenlet = self.spawn(self.run)

    def stop(self):
        if not self.greenlet:
            return
        self.should_stop = True
        self.greenlet.join()
        self.greenlet = None


class KombuEventSystem(BaseEventSystem):
    def __init__(self, connection, exchange_name, serializer=DEFAULT_SERIALIZER):
        self.connection = connection
        self.exchange = kombu.Exchange(exchange_name, 'topic', durable=True)
        self.greenlets = gevent.pool.Group()
        self.serializer = serializer
        self.consumers_by_queue = {}

    def on_stop(self):
        for consumer in self.consumers_by_queue.values():
            consumer.stop()
        self.consumers_by_queue.clear()

    @classmethod
    def from_config(cls, config, **kwargs):
        exchange_name = config.get('exchange', DEFAULT_EXCHANGE)
        serializer = config.get('serializer', DEFAULT_SERIALIZER)
        connection = kombu.Connection(**config)
        return cls(connection, exchange_name, serializer=serializer, **kwargs)

    def setup_consumer(self, handler):
        with self._get_connection() as conn:
            self.exchange(conn).declare()
            queue = kombu.Queue(handler.queue_name, self.exchange, durable=True)
            queue(conn).declare()
            for event_type in handler.event_types:
                queue(conn).bind_to(exchange=self.exchange, routing_key=event_type)
        consumer = EventConsumer(self.connection, queue, handler, spawn=self.greenlets.spawn)
        self.consumers_by_queue[handler.queue_name] = consumer
        return consumer

    def subscribe(self, handler, consume=True):
        try:
            consumer = self.consumers_by_queue[handler.queue_name]
        except KeyError:
            consumer = self.setup_consumer(handler)
        else:
            if consumer.handler != handler:
                raise RuntimeError('cannot subscribe to queue %r more than once' % handler.queue_name)
        if consume:
            consumer.start()
        return consumer

    def unsubscribe(self, handler):
        queue_name = handler.queue_name
        try:
            consumer = self.consumers_by_queue[queue_name]
        except KeyError:
            raise KeyError('there is no subscription for %r' % queue_name)
        if consumer.handler != handler:
            raise KeyError('%s is not subscribed to %r' % (handler, queue_name))
        consumer.stop()
        del self.consumers_by_queue[queue_name]

    @contextmanager
    def _get_connection(self):
        with kombu.pools.connections[self.connection].acquire(block=True) as conn:
            yield conn

    def emit(self, event):
        with self._get_connection() as conn:
            producer = conn.Producer(serializer=self.serializer)
            producer.publish(event.serialize(), routing_key=event.evt_type, exchange=self.exchange, declare=[self.exchange])
