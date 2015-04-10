import json
import logging
import os
import sys
import socket

import gevent
import gevent.queue
import gevent.pool
import six

from lymph.exceptions import RegistrationFailure, SocketNotCreated
from lymph.core.components import Componentized
from lymph.core.events import Event
from lymph.core.monitoring import metrics
from lymph.core.monitoring.pusher import MonitorPusher
from lymph.core.monitoring.aggregator import Aggregator
from lymph.core.services import ServiceInstance, Service
from lymph.core.rpc import ZmqRPCServer
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


class ServiceContainer(Componentized):

    server_cls = ZmqRPCServer

    def __init__(self, ip='127.0.0.1', port=None, registry=None, events=None, node_endpoint=None, log_endpoint=None, service_name=None, debug=False, monitor_endpoint=None, pool_size=None):
        super(ServiceContainer, self).__init__()
        self.node_endpoint = node_endpoint
        self.log_endpoint = log_endpoint
        self.backdoor_endpoint = None
        self.service_name = service_name
        self.fqdn = socket.getfqdn()

        self.service_registry = registry
        self.event_system = events

        self.error_hook = Hook()
        self.pool = trace.Group(size=pool_size)

        self.installed_interfaces = {}
        self.installed_plugins = []

        self.debug = debug
        self.monitor_endpoint = monitor_endpoint

        self.metrics_aggregator = Aggregator(self._get_metrics, service=self.service_name, host=self.fqdn)

        if self.service_registry:
            self.add_component(self.service_registry)
            self.service_registry.install(self)

        if self.event_system:
            self.add_component(self.event_system)
            self.event_system.install(self)

        self.monitor = self.install(MonitorPusher, aggregator=self.metrics_aggregator, endpoint=self.monitor_endpoint, interval=5)

        self.server = self.install(self.server_cls, ip=ip, port=port)

        self.install_interface(DefaultInterface, name='lymph')

    @classmethod
    def from_config(cls, config, **explicit_kwargs):
        kwargs = dict(config)
        kwargs.pop('class', None)
        kwargs.setdefault('node_endpoint', os.environ.get('LYMPH_NODE'))
        kwargs.setdefault('monitor_endpoint', os.environ.get('LYMPH_MONITOR'))
        kwargs.setdefault('service_name', os.environ.get('LYMPH_SERVICE_NAME'))

        for key, value in six.iteritems(explicit_kwargs):
            if value is not None:
                kwargs[key] = value
        return cls(**kwargs)

    def excepthook(self, type, value, traceback):
        logger.log(logging.CRITICAL, 'Uncaught exception', exc_info=(type, value, traceback))
        self.error_hook((type, value, traceback))

    @property
    def endpoint(self):
        return self.server.endpoint

    @property
    def identity(self):
        return self.server.identity

    def spawn(self, func, *args, **kwargs):
        def _inner():
            try:
                return func(*args, **kwargs)
            except gevent.GreenletExit:
                raise
            except:
                self.error_hook(sys.exc_info())
                raise
        return self.pool.spawn(_inner)

    def install_interface(self, cls, **kwargs):
        interface = self.install(cls, **kwargs)
        self.installed_interfaces[interface.name] = interface
        for plugin in self.installed_plugins:
            plugin.on_interface_installation(interface)
        return interface

    def install_plugin(self, cls, **kwargs):
        plugin = self.install(cls, **kwargs)
        self.installed_plugins.append(plugin)
        return plugin

    def get_shared_socket_fd(self, port):
        fds = json.loads(os.environ.get('LYMPH_SHARED_SOCKET_FDS', '{}'))
        try:
            return fds[str(port)]
        except KeyError:
            raise SocketNotCreated

    @property
    def service_types(self):
        return self.installed_interfaces.keys()

    def subscribe(self, handler, **kwargs):
        return self.event_system.subscribe(handler, **kwargs)

    def unsubscribe(self, handler):
        self.event_system.unsubscribe(handler)

    def get_instance_description(self, service_type=None):
        return {
            'endpoint': self.endpoint,
            'identity': self.identity,
            'log_endpoint': self.log_endpoint,
            'backdoor_endpoint': self.backdoor_endpoint,
            'fqdn': self.fqdn,
        }

    def start(self, register=True):
        logger.info('starting %s (%s) at %s (pid=%s)', self.service_name, ', '.join(self.service_types), self.endpoint, os.getpid())

        self.on_start()
        self.metrics_aggregator.add_tags(identity=self.identity)

        if register:
            for interface_name, service in six.iteritems(self.installed_interfaces):
                if not service.register_with_coordinator:
                    continue
                try:
                    self.service_registry.register(interface_name)
                except RegistrationFailure:
                    logger.error("registration failed %s, %s", interface_name, service)
                    self.stop()

    def stop(self, **kwargs):
        self.on_stop()
        self.pool.kill()

    def join(self):
        self.pool.join()

    def connect(self, endpoint):
        for service in six.itervalues(self.installed_interfaces):
            service.on_connect(endpoint)
        return self.server.connect(endpoint)

    def disconnect(self, endpoint, socket=False):
        self.server.disconnect(endpoint, socket)

        for service in six.itervalues(self.installed_interfaces):
            service.on_disconnect(endpoint)

    @staticmethod
    def prepare_headers(headers):
        headers = headers or {}
        headers.setdefault('trace_id', trace.get_id())
        return headers

    def lookup(self, address):
        if '://' not in address:
            return self.service_registry.get(address)
        instance = ServiceInstance(self, address)
        return Service(self, address, instances=[instance])

    def discover(self):
        return self.service_registry.discover()

    def emit_event(self, event_type, payload, headers=None, **kwargs):
        headers = self.prepare_headers(headers)
        event = Event(event_type, payload, source=self.identity, headers=headers)
        self.event_system.emit(event, **kwargs)

    def send_request(self, address, subject, body, headers=None):
        return self.server.send_request(address, subject, body, headers=None)

    def _get_metrics(self):
        for metric in super(ServiceContainer, self)._get_metrics():
            yield metric
        yield metrics.RawMetric('greenlets.count', len(self.pool))
