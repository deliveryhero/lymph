import textwrap
import logging

import six
import semantic_version

from lymph.core.components import Component, Componentized, ComponentizedBase
from lymph.core.decorators import rpc, RPCBase
from lymph.core.events import TaskHandler, EventHandler
from lymph.core.monitoring import metrics
from lymph.exceptions import RemoteError, EventHandlerTimeout, Timeout, Nack
from lymph.utils import hash_id
from lymph.core.versioning import serialize_version

import gevent
from gevent.event import AsyncResult


logger = logging.getLogger(__name__)
REQUEST_TIMEOUT = 3  # seconds.


class AsyncResultWrapper(object):
    def __init__(self, container, handler, async_result):
        self.container = container
        self.handler = handler
        self.result = async_result

    def get(self, timeout=REQUEST_TIMEOUT):
        try:
            return self.result.get(timeout=timeout)
        except gevent.Timeout:
            self.container.unsubscribe(self.handler)
            raise EventHandlerTimeout


class InterfaceBase(ComponentizedBase):
    def __new__(cls, clsname, bases, attrs):
        methods = {}
        event_handlers = {}
        is_worker = False
        for base in bases:
            if isinstance(base, InterfaceBase):
                methods.update(base.methods)
                is_worker |= base.worker
        for name, value in six.iteritems(attrs):
            if isinstance(value, RPCBase):
                methods[name] = value
            if issubclass(getattr(value, 'cls', object), EventHandler):
                event_handlers[name] = value
            if issubclass(getattr(value, 'cls', object), TaskHandler):
                is_worker = True
        new_cls = super(InterfaceBase, cls).__new__(cls, clsname, bases, attrs)
        new_cls.methods = methods
        new_cls.event_handlers = event_handlers
        new_cls.worker = is_worker
        return new_cls


class DeferredReply(AsyncResult):
    def __init__(self, subject):
        super(DeferredReply, self).__init__()
        self.subject = subject


class ProxyMethod(object):
    def __init__(self, proxy, subject):
        self.proxy = proxy
        self.subject = subject

    def __call__(self, **kwargs):
        return self.proxy._call(self.subject, **kwargs)

    def defer(self, *args, **kwargs):
        result = DeferredReply(self.subject)
        self.proxy.spawn(self, *args, **kwargs).link(result)
        return result


class Proxy(Component):
    def __init__(self, container, address, timeout=REQUEST_TIMEOUT, namespace='', version=None, error_map=None):
        super(Proxy, self).__init__()
        self._container = container
        self._address = address
        self._method_cache = {}
        self._timeout = timeout
        self._namespace = namespace or address
        if version and not isinstance(version, semantic_version.Version):
            version = semantic_version.Version.coerce(version)
        self._version = version
        self._error_map = error_map or {}

    def on_start(self):
        super(Proxy, self).on_start()
        self.timeout_counts = self.metrics.add(metrics.Counter('rpc.timeout_count', {'address': self._address}))
        self.exception_counts = self.metrics.add(metrics.TaggedCounter('rpc.exception_count', {'address': self._address}))

    def _call(self, __name, **kwargs):
        channel = self._container.send_request(self._address, __name, kwargs, version=self._version)
        try:
            return channel.get(timeout=self._timeout).body
        except RemoteError as e:
            error_type = str(e.__class__)
            self.exception_counts.incr(name=e.__class__.__name__)
            if error_type in self._error_map:
                raise self._error_map[error_type]()
            raise
        except Timeout:
            self.timeout_counts += 1
            raise
        except Nack:
            self.exception_counts.incr(name='nack')
            raise

    def __getattr__(self, name):
        try:
            return self._method_cache[name]
        except KeyError:
            method = ProxyMethod(self, '%s.%s' % (self._namespace, name))
            self._method_cache[name] = method
            return method


@six.add_metaclass(InterfaceBase)
class Interface(Componentized):
    def __init__(self, container, name=None, builtin=False, version=None):
        super(Interface, self).__init__()
        self.container = container
        self.name = name or self.__class__.__name__
        self.base_name = self.name
        self.builtin = builtin
        self.version = version
        if container.worker and not builtin:
            self.name = '%s.worker' % self.name

    def __str__(self):
        return '%s@%s' % (self.name, self.version)

    @property
    def id(self):
        return hash_id(self.container.identity, self.name, self.version)

    def should_register(self):
        return True

    def should_install(self):
        return not self.container.worker or self.worker or self.builtin

    def apply_config(self, config):
        self.config = config

    def get_description(self):
        return {}

    def handle_request(self, func_name, channel):
        method = self.methods[func_name]
        channel.add_header('version', serialize_version(self.version))
        method.rpc_call(self, channel, **channel.request.body)

    def request(self, address, subject, body, timeout=REQUEST_TIMEOUT, version=None):
        channel = self.container.send_request(address, subject, body, version=version)
        return channel.get(timeout=timeout)

    def emit(self, event_type, payload, delay=0):
        self.container.emit_event(event_type, payload, delay=delay)

    def proxy(self, address, **kwargs):
        proxy = Proxy(self.container, address, **kwargs)
        self.add_component(proxy)
        return proxy

    def subscribe(self, *event_types, **kwargs):
        def decorator(func):
            from lymph.core.events import EventHandler
            handler = EventHandler(self, func, event_types, **kwargs)
            self.container.subscribe(handler)
            return handler
        return decorator

    def get_next_event(self, *event_types, **kwargs):
        kwargs['once'] = True
        result = AsyncResult()

        @self.subscribe(*event_types, **kwargs)
        def handler(interface, event):
            result.set(event.body)

        return AsyncResultWrapper(self.container, handler, result)


class DefaultInterface(Interface):
    @rpc()
    def ping(self, payload=None):
        return payload

    @rpc()
    def status(self):
        return {
            'endpoint': self.container.endpoint,
            'identity': self.container.identity,
        }

    @rpc()
    def inspect(self):
        """
        Returns a description of all available rpc methods of this service
        """
        methods = []
        for interface in list(self.container.iter_interfaces()):
            for name, func in six.iteritems(interface.methods):
                methods.append({
                    'name': '%s.%s' % (interface.name, name),
                    'version': str(interface.version),
                    'params': list(func.args.args),
                    'help': textwrap.dedent(func.__doc__ or '').strip(),
                })
        return {
            'methods': methods,
        }

    @rpc()
    def change_loglevel(self, qualname, loglevel, period=60):
        curr_logger = logging.getLogger(qualname)

        def reset():
            logger.info("Resetting logger %s level to %s", qualname, self.container.loglevel)
            curr_logger.setLevel(self.container.loglevel)

        gevent.spawn_later(period, reset)
        curr_logger.setLevel(loglevel)
        logger.info("Changing logger %s level to %s", qualname, loglevel)

    @rpc()
    def get_metrics(self):
        return list(self.container.metrics)
