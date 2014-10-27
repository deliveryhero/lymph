import collections
import errno
import json
import gc
import gevent
import gevent.queue
import gevent.pool
import hashlib
import logging
import random
import os
import six
import sys
import zmq.green as zmq

from lymph.exceptions import RegistrationFailure, SocketNotCreated, NotConnected
from lymph.core.connection import Connection
from lymph.core.channels import RequestChannel, ReplyChannel
from lymph.core.events import Event
from lymph.core.messages import Message
from lymph.core.monitoring import Monitor
from lymph.core.services import ServiceInstance
from lymph.core.interfaces import DefaultInterface
from lymph.core.plugins import Hook
from lymph.core import trace


logger = logging.getLogger(__name__)


def create_container(config):
    registry = config.create_instance('registry')
    event_system = config.create_instance('event_system')
    container = config.create_instance(
        'container',
        default_class='lymph.core.container:ServiceContainer',
        registry=registry,
        events=event_system,
    )
    return container


class ServiceContainer(object):
    def __init__(self, ip='127.0.0.1', port=None, registry=None, logger=None, events=None, node_endpoint=None, log_endpoint=None, service_name=None):
        self.zctx = zmq.Context.instance()
        self.ip = ip
        self.port = port
        self.node_endpoint = node_endpoint
        self.log_endpoint = log_endpoint
        self.endpoint = None
        self.service_name = service_name
        self.bound = False

        self.request_counts = collections.Counter()

        self.recv_loop_greenlet = None
        self.channels = {}
        self.connections = {}
        self.pool = trace.Group()
        self.service_registry = registry
        self.event_system = events

        self.bind()
        self.identity = hashlib.md5(self.endpoint.encode('utf-8')).hexdigest()
        self.installed_interfaces = {}
        self.installed_plugins = []
        self.error_hook = Hook()

        self.monitor = Monitor(self)

        self.install(DefaultInterface)
        registry.install(self)
        if events:
            events.install(self)

    def spawn(self, func, *args, **kwargs):
        return self.pool.spawn(func, *args, **kwargs)

    @classmethod
    def from_config(cls, config, **explicit_kwargs):
        kwargs = dict(config)
        kwargs.pop('class', None)
        kwargs.setdefault('node_endpoint', os.environ.get('LYMPH_NODE'))
        for key, value in six.iteritems(explicit_kwargs):
            if value is not None:
                kwargs[key] = value
        return cls(**kwargs)

    def install(self, cls, **kwargs):
        obj = cls(self, **kwargs)
        self.installed_interfaces[obj.service_type] = obj
        return obj

    def install_plugin(self, cls, **kwargs):
        plugin = cls(self, **kwargs)
        self.installed_plugins.append(plugin)

    def rpc_stats(self):
        stats = {
            'requests': dict(self.request_counts),
        }
        self.request_counts.clear()
        return stats

    def stats(self):
        hub = gevent.get_hub()
        threadpool, loop = hub.threadpool, hub.loop
        s = {
            'endpoint': self.endpoint,
            'identity': self.identity,
            'greenlets': len(self.pool),
            'service': self.service_name,
            'gevent': {
                'threadpool': {
                    'size': threadpool.size,
                    'maxsize': threadpool.maxsize,
                },
                'active': loop.activecnt,
                'pending': loop.pendingcnt,
                'iteration': loop.iteration,
                'depth': loop.depth,
            },
            'gc': {
                'garbage': len(gc.garbage),
                'collections': gc.get_count(),
            },
            'rpc': self.rpc_stats(),
            'connections': [c.stats() for c in self.connections.values()],
        }
        for name, interface in six.iteritems(self.installed_interfaces):
            s[name] = interface.stats()
        return s

    def get_shared_socket_fd(self, port):
        fds = json.loads(os.environ.get('LYMPH_SHARED_SOCKET_FDS', '{}'))
        try:
            return fds[str(port)]
        except KeyError:
            raise SocketNotCreated

    def bind(self, max_retries=2, retry_delay=0):
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

    def close_sockets(self):
        self.recv_sock.close()
        self.send_sock.close()

    @property
    def service_types(self):
        return self.installed_interfaces.keys()

    def subscribe(self, handler, **kwargs):
        return self.event_system.subscribe(handler, **kwargs)

    def unsubscribe(self, handler):
        self.event_system.unsubscribe(self, handler)

    def get_instance_description(self, service_type=None):
        return {
            'endpoint': self.endpoint,
            'identity': self.identity,
            'log_endpoint': self.log_endpoint,
        }

    def start(self, register=True):
        self.running = True
        logger.info('starting %s at %s (pid=%s)', ', '.join(self.service_types), self.endpoint, os.getpid())
        self.recv_loop_greenlet = self.spawn(self.recv_loop)
        self.monitor.start()
        self.service_registry.on_start()
        self.event_system.on_start()

        for service in six.itervalues(self.installed_interfaces):
            service.on_start()
            service.configure({})

        if register:
            for service_type, service in six.iteritems(self.installed_interfaces):
                if not service.register_with_coordinator:
                    continue
                try:
                    self.service_registry.register(service_type)
                except RegistrationFailure:
                    logger.info("registration failed %s, %s", service_type, service)
                    self.stop()

    def stop(self):
        self.running = False
        for service in six.itervalues(self.installed_interfaces):
            service.on_stop()
        self.event_system.on_stop()
        self.service_registry.on_stop()
        self.monitor.stop()
        for connection in list(self.connections.values()):
            connection.close()
        self.recv_loop_greenlet.kill()
        self.pool.kill()
        self.close_sockets()

    def join(self):
        self.pool.join()
        self.recv_loop_greenlet.join()

    def connect(self, endpoint):
        if endpoint not in self.connections:
            logger.debug("connect(%s)", endpoint)
            self.connections[endpoint] = Connection(self, endpoint)
            self.send_sock.connect(endpoint)
            for service in six.itervalues(self.installed_interfaces):
                service.on_connect(endpoint)
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
        for service in six.itervalues(self.installed_interfaces):
            service.on_disconnect(endpoint)

    def lookup(self, address):
        if '://' not in address:
            return self.service_registry.get(address)
        return ServiceInstance(self, address)

    def discover(self):
        return self.service_registry.discover()

    def send_message(self, address, msg):
        if not self.running:
            logger.info('cannot send message (container not started): %s', msg)
            return
        service = self.lookup(address)
        try:
            connection = service.connect()
        except NotConnected:
            logger.info('cannot send message (no connection): %s', msg)
            return
        self.send_sock.send(connection.endpoint.encode('utf-8'), flags=zmq.SNDMORE)
        self.send_sock.send_multipart(msg.pack_frames())
        logger.debug('-> %s to %s', msg, connection.endpoint)
        connection.on_send(msg)

    def prepare_headers(self, headers):
        headers = headers or {}
        headers.setdefault('trace_id', trace.get_id())
        return headers

    def send_request(self, address, subject, body, headers=None):
        msg = Message(
            msg_type=Message.REQ,
            subject=subject,
            body=body,
            source=self.endpoint,
            headers=self.prepare_headers(headers),
        )
        channel = RequestChannel(msg, self)
        self.channels[msg.id] = channel
        self.send_message(address, msg)
        return channel

    def send_reply(self, msg, body, msg_type=Message.REP, headers=None):
        reply_msg = Message(
            msg_type=msg_type,
            subject=msg.id,
            body=body,
            source=self.endpoint,
            headers=self.prepare_headers(headers),
        )
        self.send_message(msg.source, reply_msg)
        return reply_msg

    def dispatch_request(self, msg):
        self.request_counts[msg.subject] += 1
        channel = ReplyChannel(msg, self)
        service_name, func_name = msg.subject.rsplit('.', 1)
        try:
            service = self.installed_interfaces[service_name]
        except KeyError:
            logger.warning('unsupported service type: %s', service_name)
            return
        try:
            service.handle_request(func_name, channel)
        except Exception:
            logger.exception('')
            exc_info = sys.exc_info()
            try:
                self.error_hook(exc_info)
            except:
                logger.exception('error hook failure')
            finally:
                del exc_info
            try:
                channel.nack(True)
            except:
                logger.exception('failed to send automatic NACK')

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

    def recv_loop(self):
        while True:
            frames = self.recv_sock.recv_multipart()
            try:
                msg = Message.unpack_frames(frames)
            except ValueError as e:
                msg_id = frames[1] if len(frames) >= 2 else None
                logger.warning('bad message format %s: %r (msg-id=%s)', e, (frames), msg_id)
                continue
            self.recv_message(msg)

    def emit_event(self, event_type, payload, headers=None):
        headers = self.prepare_headers(headers)
        event = Event(event_type, payload, source=self.identity, headers=headers)
        self.event_system.emit(event)

    def ping(self, address):
        return self.send_request(address, 'lymph.ping', {'payload': ''})
