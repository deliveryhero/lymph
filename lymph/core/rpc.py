import errno
import hashlib
import logging
import random
import time

import gevent
import zmq.green as zmq

from lymph.core.channels import RequestChannel, ReplyChannel
from lymph.core.components import Component
from lymph.core.connection import Connection
from lymph.core.messages import Message
from lymph.core.monitoring import metrics
from lymph.core.services import Service
from lymph.core import services
from lymph.core import trace
from lymph.exceptions import NotConnected


logger = logging.getLogger(__name__)


class ZmqRPCServer(Component):
    def __init__(self, ip='127.0.0.1', port=None, pool=None):
        super(ZmqRPCServer, self).__init__(pool=pool)
        self.ip = ip
        self.port = port

        self.zctx = zmq.Context.instance()
        self.endpoint = None
        self.bound = False
        self.request_counts = metrics.TaggedCounter('rpc')
        self.recv_loop_greenlet = None
        self.channels = {}
        self.connections = {}
        self.running = False
        self.request_handler = lambda channel: None

    @classmethod
    def from_config(cls, config, **kwargs):
        if 'pool' in config:
            pool = config.create_instance('pool', default_class='lymph.core.trace:Group')
        else:
            pool = None
        return cls(
            ip=config.get('ip', kwargs.get('ip') or '127.0.0.1'),
            port=config.get('port', kwargs.get('port')),
            pool=pool,
        )

    @property
    def identity(self):
        if self.endpoint:
            return hashlib.md5(self.endpoint.encode('utf-8')).hexdigest()

    def _bind(self, max_retries=2, retry_delay=0):
        assert not self.bound, 'already bound (endpoint=%s)' % self.endpoint
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
            logger.debug("connecting to %s", endpoint)
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
        logger.debug("disconnecting from %s", endpoint)
        if socket:
            self.send_sock.disconnect(endpoint)

    def on_start(self):
        self._bind()
        self.running = True
        self.recv_loop_greenlet = self.spawn(self._recv_loop)

    def on_stop(self, **kwargs):
        self.running = False
        for connection in list(self.connections.values()):
            connection.close()
        if self.recv_loop_greenlet:
            self.recv_loop_greenlet.kill()
        self._close_sockets()

    def _close_sockets(self):
        self.recv_sock.close()
        self.send_sock.close()

    def _on_service_instance_unavailable(self, instance, action=None):
        self.disconnect(instance.endpoint)

    def _send_message(self, endpoint, msg):
        if not self.running:
            # FIXME: This should raise an Error instead of failing silently.
            logger.error('cannot send message (not started): %s', msg)
            return
        connection = self.connect(endpoint)
        self.send_sock.send(endpoint.encode('utf-8'), flags=zmq.SNDMORE)
        self.send_sock.send_multipart(msg.pack_frames())
        logger.debug('-> %s to %s', msg, endpoint)
        connection.on_send(msg)

    def prepare_headers(self, headers):
        headers = headers or {}
        headers.setdefault('trace_id', trace.get_id())
        return headers

    def _pick_endpoint(self, service):
        if not isinstance(service, Service):
            return service
        service.observe(services.REMOVED, self._on_service_instance_unavailable)
        choices = []
        for instance in service:
            try:
                connection = self.connections[instance.endpoint]
            except KeyError:
                choices.append(instance.endpoint)
                continue
            if connection.is_alive():
                choices.append(instance.endpoint)
        if not choices:
            raise NotConnected('Not connected to %s' % service.name)
        return random.choice(choices)

    def send_request(self, service, subject, body, headers=None):
        msg = Message(
            msg_type=Message.REQ,
            subject=subject,
            body=body,
            source=self.endpoint,
            headers=self.prepare_headers(headers),
        )
        channel = RequestChannel(msg, self)
        self.channels[msg.id] = channel
        try:
            endpoint = self._pick_endpoint(service)
        except NotConnected:
            logger.error('cannot send message (no instance): %s', msg)
        else:
            self._send_message(endpoint, msg)
        return channel

    def send_reply(self, msg, body, msg_type=Message.REP, headers=None):
        reply_msg = Message(
            msg_type=msg_type,
            subject=msg.id,
            body=body,
            source=self.endpoint,
            headers=self.prepare_headers(headers),
        )
        self._send_message(msg.source, reply_msg)
        return reply_msg

    def dispatch_request(self, msg):
        loglevel = self._get_loglevel(msg)
        logger.log(loglevel, '%s source=%s', msg.subject, msg.source)
        start = time.time()
        self.request_counts.incr(subject=msg.subject)
        channel = ReplyChannel(msg, self)
        try:
            self.request_handler(channel)
        finally:
            elapsed = time.time() - start
            logger.log(loglevel, 'subject=%s duration=%f (seconds)', msg.subject, elapsed)

    def _get_loglevel(self, msg):
        return logging.DEBUG if msg.subject == 'lymph.ping' else logging.INFO

    def recv_message(self, msg):
        trace.set_id(msg.headers.get('trace_id'))
        logger.debug('<- %s', msg)
        connection = self.connect(msg.source)
        connection.on_recv(msg)
        if msg.is_request():
            self.spawn(self.dispatch_request, msg)
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

    def _get_metrics(self):
        yield metrics.RawMetric('rpc.connection_count', len(self.connections))
        yield self.request_counts
