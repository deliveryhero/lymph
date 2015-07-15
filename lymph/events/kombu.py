from __future__ import absolute_import

import sys
from contextlib import contextmanager
from collections import namedtuple

import logging
import kombu
import kombu.mixins
import kombu.pools

from lymph.events.base import BaseEventSystem
from lymph.core.events import Event
from lymph.utils.logging import setup_logger


logger = logging.getLogger(__name__)


DEFAULT_SERIALIZER = 'lymph-msgpack'
DEFAULT_EXCHANGE = 'lymph'
DEFAULT_MAX_RETRIES = 3

# Info of where the queue master server, so that we can redeclare the queue
# when we failover to another master.
QueueInfo = namedtuple('QueueInfo', 'master queue')


class EventConsumer(kombu.mixins.ConsumerMixin):
    def __init__(self, event_system, connection, queue, handler, exchange, max_retries=DEFAULT_MAX_RETRIES):
        self.connection = connection
        self.queue = queue
        self.handler = handler
        self.exchange = exchange
        self.greenlet = None
        self.event_system = event_system
        self.connect_max_retries = max_retries

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=[self.queue], callbacks=[self.on_kombu_message])]

    def create_connection(self):
        return kombu.pools.connections[self.connection].acquire()

    def on_connection_revived(self):
        # Re-create any queue and bind it to exchange in case of a failover, Since
        # the bind may be broken or the queue my have been deleted if it was created
        # with auto-delete.
        self._declare()

    def _declare(self):
        with self.establish_connection() as conn:
            self.event_system.safe_declare(conn, self.queue)
            for event_type in self.handler.event_types:
                self.queue(conn).bind_to(exchange=self.exchange, routing_key=event_type)

    def on_kombu_message(self, body, message):
        logger.debug("received kombu message %r", body)
        if self.handler.sequential:
            self._handle_message(body, message)
        else:
            self.event_system.container.spawn(self._handle_message, body, message)

    def _handle_message(self, body, message):
        try:
            event = Event.deserialize(body)
            self.handler(event)
            message.ack()
        except:
            logger.exception('failed to handle event from queue %r', self.handler.queue_name)
            # FIXME: add requeue support here. Make sure what we don't requeue
            # forever.
            message.reject()
            self.event_system.container.error_hook(sys.exc_info())
        finally:
            if self.handler.once:
                self.event_system.unsubscribe(self.handler)

    def start(self):
        if self.greenlet:
            return
        self.should_stop = False
        self._declare()
        self.greenlet = self.event_system.container.spawn(self.run)

    def stop(self, **kwargs):
        if not self.greenlet:
            return
        self.should_stop = True
        self.greenlet.join()
        self.greenlet = None


class EventProducer(object):
    def __init__(self, event_system, event_type, max_retries=DEFAULT_MAX_RETRIES):
        self.event_system = event_system
        self.routing_key = event_type
        self.exchange = self.event_system.exchange
        self.serializer = self.event_system.serializer
        self.max_retries = max_retries

    @contextmanager
    def _get_connection(self):
        with self.event_system.get_connection() as conn:
            yield conn

    def _get_producer(self, conn):
        return conn.Producer(
            serializer=self.serializer, routing_key=self.routing_key,
            exchange=self.exchange)

    def emit(self, event):
        with self._get_connection() as conn:
            producer = self._get_producer(conn)
            return producer.publish(event.serialize(), retry_policy={'max_retries': self.max_retries})


class EventProducerWithDelay(EventProducer):
    """Producer that allow sending messages after a given delay.

    It works by publishing messages to an intermediate RabbitMQ queue, this messages
    will have a ttl set to the delay given, this way RabbitMQ will forward the messages
    after the ttl expire to the dead-letter-exchange attached to the intermediate queue,
    which we set to our main exchange (i.e. default to 'lymph' exchange), et voila now
    RabbitMQ can send the message to the lymph events handler.
    """

    def __init__(self, delay, *args, **kwargs):
        super(EventProducerWithDelay, self).__init__(*args, **kwargs)
        self.delay = delay  # Delay in ms.
        self.exchange = kombu.Exchange('%s_waiting' % self.event_system.exchange_name, 'direct', durable=True)
        self._intermediate_queue = None

    def _get_producer(self, conn):
        if self._intermediate_queue is None or self._intermediate_queue.master != conn.as_uri():
            queue = self._prepare_intermediate_queue(conn)
            self._intermediate_queue = QueueInfo(master=conn.as_uri(), queue=queue)
        return super(EventProducerWithDelay, self)._get_producer(conn)

    def _prepare_intermediate_queue(self, conn):
        queue_name = '%s-wait_%s' % (self.routing_key, self.delay)
        queue = self.event_system.get_queue(queue_name, durable=False, queue_arguments={
            'x-dead-letter-exchange': self.event_system.exchange.name,
            'x-dead-letter-routing-key': self.routing_key,
            'x-message-ttl': self.delay,
        })
        self.exchange(conn).declare()
        self.event_system.safe_declare(conn, queue)
        queue(conn).bind_to(exchange=self.exchange, routing_key=self.routing_key)
        return queue


class KombuEventSystem(BaseEventSystem):
    def __init__(self, connection, exchange_name, serializer=DEFAULT_SERIALIZER, connect_max_retries=DEFAULT_MAX_RETRIES):
        super(KombuEventSystem, self).__init__()
        self.connection = connection
        self.exchange_name = exchange_name
        self.exchange = kombu.Exchange(exchange_name, 'topic', durable=True)
        self.serializer = serializer
        self.connect_max_retries = connect_max_retries
        self._producers = {}
        self.consumers_by_queue = {}

    @classmethod
    def from_config(cls, config, **kwargs):
        exchange_name = config.get('exchange', DEFAULT_EXCHANGE)
        serializer = config.get('serializer', DEFAULT_SERIALIZER)
        connection = kombu.Connection(**config)
        return cls(connection, exchange_name, serializer=serializer, **kwargs)

    def on_start(self):
        setup_logger('kombu')

    def on_stop(self, **kwargs):
        for consumer in self.consumers_by_queue.values():
            consumer.stop(**kwargs)
        self.consumers_by_queue.clear()

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

    def setup_consumer(self, handler):
        with self.get_connection() as conn:
            self.exchange(conn).declare()
            if handler.broadcast:
                queue = self.get_queue(handler.queue_name, auto_delete=True, durable=False)
            else:
                queue = self.get_queue(handler.queue_name, auto_delete=handler.once, durable=False)
        consumer = EventConsumer(self, self.connection, queue, handler, self.exchange, max_retries=self.connect_max_retries)
        self.consumers_by_queue[handler.queue_name] = consumer
        return consumer

    @contextmanager
    def get_connection(self):
        with kombu.pools.connections[self.connection].acquire() as conn:
            conn.ensure_connection(max_retries=self.connect_max_retries)
            logger.debug('connecting to %s', conn.as_uri())
            yield conn

    @staticmethod
    def get_queue(name, **kwargs):
        queue_arguments = kwargs.pop('queue_arguments', {})
        queue_arguments['x-ha-policy'] = 'all'
        return kombu.Queue(name, queue_arguments=queue_arguments, **kwargs)

    @staticmethod
    def safe_declare(conn, queue):
        try:
            queue(conn).declare()
        except conn.connection.channel_errors as exc:
            # XXX(Mouad): Redeclare queue since a race condition may happen
            # when declaring queues in failover situation, more info check:
            # https://bugs.launchpad.net/neutron/+bug/1318721.
            queue(conn).declare()

    def emit(self, event, delay=0):
        producer = self._get_producer(event.evt_type, delay)
        producer.emit(event)

    def _get_producer(self, event_type, delay=0):
        try:
            return self._producers[event_type, delay]
        except KeyError:
            if delay:
                producer = EventProducerWithDelay(int(1000 * delay), self, event_type)
            else:
                producer = EventProducer(self, event_type)
        self._producers[event_type, delay] = producer
        return producer
