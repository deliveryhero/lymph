import gevent
import gevent.socket
import msgpack
import redis
import logging

from lymph.exceptions import RpcError, Timeout
from lymph.core.interfaces import Interface
from lymph.core.decorators import rpc


logger = logging.getLogger(__name__)


class Broker(Interface):
    service_type = 'broker'

    def __init__(self, *args, **kwargs):
        super(Broker, self).__init__(*args, **kwargs)
        self.redis = redis.StrictRedis()

    def configure(self, config):
        super(Broker, self).configure(config)
        self.config['broadcast_map'] = {
            'alarm': set(['lymph://echo']),
            'uppercase_transform_finished': set(['lymph://demo']),
        }

    def on_start(self):
        self.recover()

    @rpc()
    def broadcast(self, channel, event_type=None, payload=None):
        pipe = self.redis.pipeline()
        broadcast_map = self.config.get('broadcast_map', {})
        for endpoint in broadcast_map.get(event_type):
            pipe.sadd(endpoint, msgpack.dumps(channel.request.body))
            pipe.sadd('queues', endpoint)
        with gevent.Timeout(1, Timeout(channel.request)):
            result = pipe.execute()
            logger.debug('Redis pipe %r', result)
        channel.ack()
        # FIXME: complain if event_type is None
        for endpoint in broadcast_map.get(event_type):
            self.container.spawn(self.relay_msg, endpoint, channel.request.body)

    def relay_msg(self, endpoint, msg_body):
        while True:
            try:
                self.request(endpoint, 'simple_broker_client.event', msg_body)
            except RpcError:
                # FIXME: Use a proper retry strategy
                gevent.sleep(1)
            else:
                self.redis.srem(endpoint, msgpack.dumps(msg_body))
                break

    def recover(self):
        for endpoint in self.redis.smembers('queues'):
            queue = self.redis.smembers(endpoint)
            if not queue:
                self.redis.srem('queues', endpoint)
            for raw_msg in queue:
                # TODO: Why is this not using the normal serializer?
                self.container.spawn(
                    self.relay_msg,
                    endpoint.decode('utf-8'),
                    msgpack.loads(raw_msg, encoding='utf-8'))
