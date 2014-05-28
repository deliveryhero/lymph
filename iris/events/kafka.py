from __future__ import absolute_import

import json
import gevent

from kafka import KafkaClient
from kafka.client import FailedPayloadsException
from kafka.consumer import SimpleConsumer
from kafka.producer import SimpleProducer

from iris.events.base import BaseEventSystem
from iris.core.events import Event


class KafkaEventSystem(BaseEventSystem):
    def __init__(self):
        self.client = KafkaClient("localhost", 9092)
        self.producers = {}

    def _consume(self, consumer, container, event_type):
        for event in consumer:
            event = Event.deserialize(json.loads(event.message.value))
            container.handle_event(event)

    def subscribe(self, container, event_type):
        consumer = SimpleConsumer(self.client, 'foo', event_type)
        gevent.spawn(self._consume, consumer, container, event_type)

    def unsubscribe(self, container, event_type):
        pass

    def emit(self, container, event):
        try:
            producer = self.producers[event.evt_type]
        except KeyError:
            producer = SimpleProducer(self.client, event.evt_type)
            self.producers[event.evt_type] = producer
        producer.send_messages(json.dumps(event.serialize()))
