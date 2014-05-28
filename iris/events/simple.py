from iris.core.interfaces import Interface
from iris.core.decorators import rpc
from iris.events.base import BaseEventSystem
from iris.core.events import Event


class SimpleBrokerClient(Interface):
    service_type = 'simple_broker_client'
    register_with_coordinator = False

    @rpc()
    def event(self, channel, event_type=None, payload=None):
        """
        Receive an event of type `event_type` with the given `payload`. This
        is used by the simple event system in iris.events.simple:Broker
        """
        event = Event(event_type, payload)
        try:
            self.container.handle_event(event)
        except:
            raise
        else:
            channel.ack()


class SimpleEventSystem(BaseEventSystem):
    def install(self, container):
        container.install(SimpleBrokerClient)

    def subscribe(self, container, event_type):
        pass

    def unsubscribe(self, container, event_type):
        pass

    def emit(self, container, event, timeout=1):
        channel = container.send_request('iris://broker', 'broker.broadcast', {
            'event_type': event.evt_type,
            'payload': event.body,
        })
        channel.get(timeout=1)
