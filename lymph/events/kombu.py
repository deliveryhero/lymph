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

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=[self.queue], callbacks=[self.on_kombu_message])]

    def create_connection(self):
        return kombu.pools.connections[self.connection].acquire(block=True)

    def on_kombu_message(self, body, message):
        logger.debug("received kombu message %r", body)

        def message_handler():
            event = Event.deserialize(body)
            try:
                self.handler(event)
            except:
                raise
            else:
                message.ack()
        if self.handler.sequential:
            message_handler()
        else:
            self.spawn(message_handler)

    def start(self):
        self.should_stop = False
        self.greenlet = self.spawn(self.run)

    def stop(self):
        self.should_stop = True
        self.greenlet.join()


class KombuEventSystem(BaseEventSystem):
    def __init__(self, connection, exchange_name, serializer=DEFAULT_SERIALIZER):
        self.connection = connection
        self.exchange = kombu.Exchange(exchange_name, 'topic', durable=True)
        self.greenlets = gevent.pool.Group()
        self.serializer = serializer
        self.consumers = set()

    def on_stop(self):
        for consumer in self.consumers:
            consumer.stop()

    @classmethod
    def from_config(cls, config, **kwargs):
        exchange_name = config.get('exchange', DEFAULT_EXCHANGE)
        serializer = config.get('serializer', DEFAULT_SERIALIZER)
        connection = kombu.Connection(**config)
        return cls(connection, exchange_name, serializer=serializer, **kwargs)

    def subscribe(self, container, handler):
        with self._get_connection() as conn:
            self.exchange(conn).declare()
            queue = kombu.Queue(handler.queue_name, self.exchange, durable=True)
            queue(conn).declare()
            for event_type in handler.event_types:
                queue(conn).bind_to(exchange=self.exchange, routing_key=event_type)
        consumer = EventConsumer(self.connection, queue, handler, spawn=self.greenlets.spawn)
        self.consumers.add(consumer)
        consumer.start()

    def unsubscribe(self, container, handler):
        pass

    @contextmanager
    def _get_connection(self):
        with kombu.pools.connections[self.connection].acquire(block=True) as conn:
            yield conn

    def emit(self, container, event):
        with self._get_connection() as conn:
            producer = conn.Producer(serializer=self.serializer)
            producer.publish(event.serialize(), routing_key=event.evt_type, exchange=self.exchange, declare=[self.exchange])
