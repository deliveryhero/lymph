import gevent
import msgpack
import redis
import time

from lymph.core.interfaces import Interface
from lymph.core.decorators import rpc
from lymph.utils import make_id


class Scheduler(Interface):
    service_type = 'scheduler'
    schedule_key = 'schedule'

    def __init__(self, *args, **kwargs):
        super(Scheduler, self).__init__(*args, **kwargs)
        self.redis = redis.StrictRedis()

    def on_start(self):
        self.container.spawn(self.loop)

    @rpc()
    def schedule(self, eta, event_type, payload):
        self.redis.zadd(self.schedule_key, eta, msgpack.dumps({
            'id': make_id(),
            'event_type': event_type,
            'payload': payload,
        }))

    def loop(self):
        while True:
            pipe = self.redis.pipeline()
            now = int(time.time())
            pipe.zrangebyscore(self.schedule_key, 0, now)
            pipe.zremrangebyscore(self.schedule_key, 0, now)
            events, n = pipe.execute()
            for event in events:
                event = msgpack.loads(event, encoding='utf-8')
                self.emit(event['event_type'], event['payload'])
            gevent.sleep(1)
