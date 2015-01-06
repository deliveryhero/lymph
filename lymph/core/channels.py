import gevent
import gevent.queue

from lymph.exceptions import Timeout, Nack, RemoteError
from lymph.core.messages import Message


class Channel(object):
    def __init__(self, request, server):
        self.request = request
        self.server = server


class RequestChannel(Channel):
    def __init__(self, request, server):
        super(RequestChannel, self).__init__(request, server)
        self.queue = gevent.queue.Queue()

    def recv(self, msg):
        self.queue.put(msg)

    def get(self, timeout=1):
        try:
            msg = self.queue.get(timeout=timeout)
            if msg.type == Message.NACK:
                raise Nack(self.request)
            elif msg.type == Message.ERROR:
                raise RemoteError.from_reply(self.request, msg)
            return msg
        except gevent.queue.Empty:
            raise Timeout(self.request)
        finally:
            self.close()

    def close(self):
        del self.server.channels[self.request.id]


class ReplyChannel(Channel):
    def __init__(self, request, server):
        super(ReplyChannel, self).__init__(request, server)
        self._sent_reply = False

    def reply(self, body):
        self.server.send_reply(self.request, body)
        self._sent_reply = True

    def ack(self, unless_reply_sent=False):
        if unless_reply_sent and self._sent_reply:
            return
        self.server.send_reply(self.request, None, msg_type=Message.ACK)
        self._sent_reply = True

    def nack(self, unless_reply_sent=False):
        if unless_reply_sent and self._sent_reply:
            return
        self.server.send_reply(self.request, None, msg_type=Message.NACK)
        self._sent_reply = True

    def error(self, **body):
        self.server.send_reply(self.request, body, msg_type=Message.ERROR)

    def close(self):
        pass
