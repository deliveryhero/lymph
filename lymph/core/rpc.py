import collections
import errno
import hashlib
import logging
import random
import sys
import time

import gevent
import zmq.green as zmq

from lymph.core.channels import RequestChannel, ReplyChannel
from lymph.core.connection import Connection
from lymph.core.messages import Message
from lymph.core import trace
from lymph.exceptions import NotConnected


logger = logging.getLogger(__name__)


class ZmqRPCServer(object):
    """RPC server using ZeroMQ."""

    def __init__(self, container, ip='127.0.0.1', port=None):
        self.container = container
        self.ip = ip
        self.port = port

        self.zctx = zmq.Context.instance()
        self.endpoint = None
        self.bound = False
        self.request_counts = collections.Counter()
        self.recv_loop_greenlet = None
        self.channels = {}
        self.connections = {}

        # FIXME: Bind in start and not here.
        self._bind()

    @property
    def identity(self):
        if self.endpoint:
            return hashlib.md5(self.endpoint.encode('utf-8')).hexdigest()

    def _bind(self, max_retries=2, retry_delay=0):
        if self.bound:
            raise TypeError('this container is already bound (endpoint=%s)', self.endpoint)
        self.send_sock = self.zctx.socket(zmq.ROUTER)
        self.recv_sock = self.zctx.socket(zmq.ROUTER)
        port = self.port
        retries = 0
        while True:
            if not self.port:
                port = random.randint(35536, 65536)
            try:
                self.endpoint = 'tcp://%s:%s' % (self.ip, port)
                endpoint = self.endpoint.encode('utf-8')
                self.recv_sock.setsockopt(zmq.IDENTITY, endpoint)
                self.send_sock.setsockopt(zmq.IDENTITY, endpoint)
                self.recv_sock.bind(self.endpoint)
            except zmq.ZMQError as e:
                if e.errno != errno.EADDRINUSE or retries >= max_retries:
                    raise
                logger.info('failed to bind to port %s (errno=%s), trying again.', port, e.errno)
                retries += 1
                if retry_delay:
                    gevent.sleep(retry_delay)
                continue
            else:
                self.port = port
                self.bound = True
                break

    def connect(self, endpoint):
        if endpoint not in self.connections:
            logger.debug("connect(%s)", endpoint)
            self.connections[endpoint] = Connection(self, endpoint)
            self.send_sock.connect(endpoint)
            gevent.sleep(0.02)
        return self.connections[endpoint]

    def disconnect(self, endpoint, socket=False):
        try:
            connection = self.connections[endpoint]
        except KeyError:
            return
        del self.connections[endpoint]
        connection.close()
        logger.debug("disconnect(%s)", endpoint)
        if socket:
            self.send_sock.disconnect(endpoint)

    def start(self):
        self.running = True
        self.recv_loop_greenlet = self.container.spawn(self._recv_loop)

    def stop(self, **kwargs):
        self.running = False
        for connection in list(self.connections.values()):
            connection.close()
        if self.recv_loop_greenlet:
            self.recv_loop_greenlet.kill()
        self._close_sockets()

    def _close_sockets(self):
        self.recv_sock.close()
        self.send_sock.close()

    def _send_message(self, address, msg):
        if not self.running:
            # FIXME: This should raise an Error instead of failing silently.
            logger.error('cannot send message (container not started): %s', msg)
            return
        service = self.container.lookup(address)
        try:
            connection = service.connect()
        except NotConnected:
            logger.error('cannot send message (no connection): %s', msg)
            return
        self.send_sock.send(connection.endpoint.encode('utf-8'), flags=zmq.SNDMORE)
        self.send_sock.send_multipart(msg.pack_frames())
        logger.debug('-> %s to %s', msg, connection.endpoint)
        connection.on_send(msg)

    def send_request(self, address, subject, body, headers=None):
        msg = Message(
            msg_type=Message.REQ,
            subject=subject,
            body=body,
            source=self.endpoint,
            headers=self.container.prepare_headers(headers),
        )
        channel = RequestChannel(msg, self)
        self.channels[msg.id] = channel
        self._send_message(address, msg)
        return channel

    def send_reply(self, msg, body, msg_type=Message.REP, headers=None):
        reply_msg = Message(
            msg_type=msg_type,
            subject=msg.id,
            body=body,
            source=self.endpoint,
            headers=self.container.prepare_headers(headers),
        )
        self._send_message(msg.source, reply_msg)
        return reply_msg

    def dispatch_request(self, msg):
        loglevel = self._get_loglevel(msg)
        logger.log(loglevel, '%s source=%s', msg.subject, msg.source)
        start = time.time()
        self.request_counts[msg.subject] += 1
        channel = ReplyChannel(msg, self)
        service_name, func_name = msg.subject.rsplit('.', 1)
        try:
            service = self.container.installed_interfaces[service_name]
        except KeyError:
            logger.warning('unsupported service type: %s', service_name)
            return
        try:
            service.handle_request(func_name, channel)
        except Exception:
            logger.exception('Request error:')
            exc_info = sys.exc_info()
            extra_info = {
                'service': service_name,
                'func_name': func_name,
                'trace_id': trace.get_id(),
            }
            try:
                self.container.error_hook(exc_info, extra=extra_info)
            except:
                logger.exception('error hook failure')
            finally:
                del exc_info
            try:
                channel.nack(True)
            except:
                logger.exception('failed to send automatic NACK')
        finally:
            elapsed = (time.time() - start) * (10 ** 3)
            logger.log(loglevel, 'subject=%s duration=%.3f (seconds)', msg.subject, elapsed)

    def _get_loglevel(self, msg):
        return logging.DEBUG if msg.subject == 'lymph.ping' else logging.INFO

    def recv_message(self, msg):
        trace.set_id(msg.headers.get('trace_id'))
        logger.debug('<- %s', msg)
        connection = self.connect(msg.source)
        connection.on_recv(msg)
        if msg.is_request():
            self.container.spawn(self.dispatch_request, msg)
        elif msg.is_reply():
            try:
                channel = self.channels[msg.subject]
            except KeyError:
                logger.debug('reply to unknown subject: %s (msg-id=%s)', msg.subject, msg.id)
                return
            channel.recv(msg)
        else:
            logger.warning('unknown message type: %s (msg-id=%s)', msg.type, msg.id)

    def _recv_loop(self):
        while True:
            frames = self.recv_sock.recv_multipart()
            try:
                msg = Message.unpack_frames(frames)
            except ValueError as e:
                msg_id = frames[1] if len(frames) >= 2 else None
                logger.warning('bad message format %s: %r (msg-id=%s)', e, (frames), msg_id)
                continue
            self.recv_message(msg)

    def ping(self, address):
        return self.send_request(address, 'lymph.ping', {'payload': ''})

    @property
    def stats(self):
        stats = {
            'rpc': {
                'requests': dict(self.request_counts)
            },
            'connections': [c.stats() for c in self.connections.values()],
        }
        self.request_counts.clear()
        return stats
