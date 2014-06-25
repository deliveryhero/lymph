import time
import gevent
import msgpack
import zmq.green as zmq


class Monitor(object):
    def __init__(self, container, monitor_endpoint='tcp://127.0.0.1:44044'):
        self.container = container
        self.stats = None
        ctx = zmq.Context.instance()
        self.socket = ctx.socket(zmq.PUB)
        self.socket.connect(monitor_endpoint)

    def start(self):
        self.loop_greenlet = self.container.spawn(self.loop)

    def stop(self):
        self.loop_greenlet.kill()

    def loop(self):
        last_stats = time.monotonic()
        while True:
            gevent.sleep(2)
            dt = time.monotonic() - last_stats
            self.stats = self.container.stats()
            self.stats.update({'dt': dt, 'time': time.time()})
            last_stats += dt
            self.socket.send_multipart([
                b'stats',
                msgpack.dumps(self.stats)])
