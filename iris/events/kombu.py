from __future__ import absolute_import

from contextlib import contextmanager

import logging
import gevent
import gevent.pool
import kombu
import kombu.mixins
import kombu.pools

from iris.events.base import BaseEventSystem
from iris.core.events import Event


logger = logging.getLogger(__name__)


DEFAULT_SERIALIZER = 'iris-msgpack'
DEFAULT_EXCHANGE = 'iris'


class EventConsumer(kombu.mixins.ConsumerMixin):
    def __init__(self, connection, queue, container):
        self.connection = connection
        self.queue = queue
        self.container = container

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=[self.queue], callbacks=[self.on_kombu_message])]

    def create_connection(self):
        return kombu.pools.connections[self.connection].acquire(block=True)

    def on_kombu_message(self, body, message):
        logger.debug("received kombu message %r", body)
        event = Event.deserialize(body)
        try:
            self.container.handle_event(event)
        except:
            raise
        else:
            message.ack()

    def start(self):
        self.should_stop = False
        self.greenlet = gevent.spawn(self.run)

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

    def subscribe(self, container, event_type):
        with self._get_connection() as conn:
            self.exchange(conn).declare()
            queue_name = '-'.join(container.service_types)
            queue = kombu.Queue(queue_name, self.exchange, durable=True)
            queue(conn).declare()
            queue(conn).bind_to(exchange=self.exchange, routing_key=event_type)
        consumer = EventConsumer(self.connection, queue, container)
        self.consumers.add(consumer)
        consumer.start()

    def unsubscribe(self, container, event_type):
        pass

    @contextmanager
    def _get_connection(self):
        with kombu.pools.connections[self.connection].acquire(block=True) as conn:
            yield conn

    def emit(self, container, event):
        with self._get_connection() as conn:
            producer = conn.Producer(serializer=self.serializer)
            producer.publish(event.serialize(), routing_key=event.evt_type, exchange=self.exchange, declare=[self.exchange])
