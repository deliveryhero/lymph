import json
import logging
import os
import sys
import socket

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
    if 'registry' in config:
        logger.warning('global `registry` configuration is deprecated. please use `container.registry` instead.')
        config.set('container.registry', config.get_raw('registry'))
    event_system = config.create_instance('event_system')
    container = config.create_instance(
        'container',
        default_class='lymph.core.container:ServiceContainer',
        events=event_system,
    )
    return container


class ServiceContainer(Componentized):
    def __init__(self, rpc=None, registry=None, events=None, log_endpoint=None, service_name=None, debug=False, monitor_endpoint=None, pool=None):
        if pool is None:
            pool = trace.Group()
        super(ServiceContainer, self).__init__(error_hook=Hook('error_hook'), pool=pool)
        self.log_endpoint = log_endpoint
        self.backdoor_endpoint = None
        self.service_name = service_name
        self.fqdn = socket.getfqdn()

        self.server = rpc
        self.service_registry = registry
        self.event_system = events

        self.installed_interfaces = {}
        self.installed_plugins = []

        self.debug = debug
        self.monitor_endpoint = monitor_endpoint

        self.metrics_aggregator = Aggregator(self._get_metrics, service=self.service_name, host=self.fqdn)

        if self.service_registry:
            self.add_component(self.service_registry)

        if self.event_system:
            self.add_component(self.event_system)
            self.event_system.install(self)

        self.monitor = self.install(MonitorPusher, aggregator=self.metrics_aggregator, endpoint=self.monitor_endpoint, interval=5)

        self.add_component(rpc)
        rpc.request_handler = self.handle_request

        self.install_interface(DefaultInterface, name='lymph')

    @classmethod
    def from_config(cls, config, **explicit_kwargs):
        kwargs = dict(config)
        kwargs.pop('class', None)
        kwargs.setdefault('monitor_endpoint', os.environ.get('LYMPH_MONITOR'))
        kwargs.setdefault('service_name', os.environ.get('LYMPH_SERVICE_NAME'))
        kwargs['registry'] = config.create_instance('registry')

        kwargs['rpc'] = config.create_instance('rpc', default_class=ZmqRPCServer, ip=kwargs.pop('ip', None), port=kwargs.pop('port', None))
        kwargs['pool'] = config.create_instance('pool', default_class='lymph.core.trace:Group')

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

    def get_instance_description(self):
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

        self.instance = ServiceInstance(**self.get_instance_description())

        if register:
            for interface_name, service in six.iteritems(self.installed_interfaces):
                if not service.register_with_coordinator:
                    continue
                try:
                    self.service_registry.register(interface_name, self.instance)
                except RegistrationFailure:
                    logger.error("registration failed %s, %s", interface_name, service)
                    self.stop()

    def stop(self, **kwargs):
        self.on_stop()
        self.pool.kill()

    def join(self):
        self.pool.join()

    def lookup(self, address):
        if '://' not in address:
            return self.service_registry.get(address)
        instance = ServiceInstance(address)
        return Service(address, instances=[instance])

    def discover(self):
        return self.service_registry.discover()

    def emit_event(self, event_type, payload, headers=None, **kwargs):
        headers = headers or {}
        headers.setdefault('trace_id', trace.get_id())
        event = Event(event_type, payload, source=self.identity, headers=headers)
        self.event_system.emit(event, **kwargs)

    def send_request(self, address, subject, body, headers=None):
        service = self.lookup(address)
        return self.server.send_request(service, subject, body, headers=headers)

    def handle_request(self, channel):
        interface_name, func_name = channel.request.subject.rsplit('.', 1)
        try:
            interface = self.installed_interfaces[interface_name]
        except KeyError:
            logger.warning('unsupported service type: %s', interface_name)
            channel.nack(True)
            return
        try:
            interface.handle_request(func_name, channel)
        except Exception:
            logger.exception('Request error:')
            exc_info = sys.exc_info()
            try:
                self.error_hook(exc_info, extra={
                    'service': self.service_name,
                    'interface': interface_name,
                    'func_name': func_name,
                    'trace_id': trace.get_id(),
                })
            finally:
                del exc_info
            try:
                channel.nack(True)
            except:
                logger.exception('failed to send automatic NACK')

    def _get_metrics(self):
        for metric in super(ServiceContainer, self)._get_metrics():
            yield metric
        yield metrics.RawMetric('greenlets.count', len(self.pool))
