import textwrap
import functools
import six

from lymph.core.decorators import rpc, RPCBase
from lymph.exceptions import RemoteError, EventHandlerTimeout
from lymph.core.declarations import Declaration

import gevent
from gevent.event import AsyncResult


class AsyncResultWrapper(object):
    def __init__(self, container, handler, async_result):
        self.container = container
        self.handler = handler
        self.result = async_result

    def get(self, timeout=30):
        try:
            return self.result.get(timeout=timeout)
        except gevent.Timeout:
            self.container.unsubscribe(self.handler)
            raise EventHandlerTimeout


class Component(object):
    def on_start(self):
        pass

    def on_stop(self, **kwargs):
        pass


class InterfaceBase(type):
    def __new__(cls, clsname, bases, attrs):
        methods = {}
        declarations = set()
        for base in bases:
            if isinstance(base, InterfaceBase):
                methods.update(base.methods)
                declarations.update(base.declarations)
        for name, value in six.iteritems(attrs):
            if isinstance(value, Declaration):
                value.name = name
                declarations.add(value)
            elif isinstance(value, RPCBase):
                methods[name] = value
        new_cls = super(InterfaceBase, cls).__new__(cls, clsname, bases, attrs)
        new_cls.methods = methods
        new_cls.declarations = declarations
        return new_cls


class ProxyMethod(object):
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def defer(self, *args, **kwargs):
        result = AsyncResult()
        gevent.spawn(self, *args, **kwargs).link(result)
        return result


class Proxy(Component):
    def __init__(self, container, address, timeout=30, namespace='', error_map=None):
        self._container = container
        self._address = address
        self._method_cache = {}
        self._timeout = timeout
        self._namespace = namespace or address
        self._error_map = error_map or {}

    def _call(self, __name, **kwargs):
        channel = self._container.send_request(self._address, __name, kwargs)
        try:
            return channel.get(timeout=self._timeout).body
        except RemoteError as e:
            error_type = str(e.__class__)
            if error_type in self._error_map:
                raise self._error_map[error_type]()
            raise

    def __getattr__(self, name):
        try:
            return self._method_cache[name]
        except KeyError:
            method = ProxyMethod(functools.partial(self._call, '%s.%s' % (self._namespace, name)))
            self._method_cache[name] = method
            return method


@six.add_metaclass(InterfaceBase)
class Interface(object):
    register_with_coordinator = True

    def __init__(self, container, name=None):
        self.container = container
        self.components = {}
        self._name = name
        for declaration in self.declarations:
            declaration.install(self)

    @property
    def name(self):
        return self._name or self.__class__.__name__

    @name.setter
    def name(self, value):
        self._name = value

    def install(self, factory):
        self.components[factory] = factory(self)

    def apply_config(self, config):
        pass

    def handle_request(self, func_name, channel):
        self.methods[func_name].rpc_call(self, channel, **channel.request.body)

    def request(self, address, subject, body, timeout=None):
        channel = self.container.send_request(address, subject, body)
        return channel.get(timeout=timeout)

    def emit(self, event_type, payload):
        self.container.emit_event(event_type, payload)

    def proxy(self, address, **kwargs):
        return Proxy(self.container, address, **kwargs)

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

    def on_start(self):
        for component in self.components.values():
            component.on_start()

    def on_stop(self, **kwargs):
        for component in self.components.values():
            component.on_stop(**kwargs)

    def on_connect(self, endpoint):
        pass

    def on_disconnect(self, endpoint):
        pass

    def stats(self):
        return {}


class DefaultInterface(Interface):
    register_with_coordinator = False

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
        for interface_name, interface in list(self.container.installed_interfaces.items()):
            for name, func in six.iteritems(interface.methods):
                methods.append({
                    'name': '%s.%s' % (interface_name, name),
                    'params': list(func.args.args),
                    'help': textwrap.dedent(func.__doc__ or '').strip(),
                })
        return {
            'methods': methods,
        }
