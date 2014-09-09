import inspect
import textwrap
import functools
import six

from lymph.core.decorators import rpc
from lymph.exceptions import ErrorReply
from lymph.core.declarations import Declaration


class Component(object):
    def on_start(self):
        pass

    def on_stop(self):
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
            elif callable(value) and getattr(value, '_rpc', False):
                methods[name] = value
        attrs.setdefault('service_type', clsname.lower())
        new_cls = super(InterfaceBase, cls).__new__(cls, clsname, bases, attrs)
        new_cls.methods = methods
        new_cls.declarations = declarations
        return new_cls


class Proxy(object):
    def __init__(self, container, address, timeout=1, namespace='', error_map=None):
        self._container = container
        self._address = address
        self._method_cache = {}
        self._timeout = timeout
        if address.startswith('lymph://') and not namespace:
            namespace = address[8:]
        self._namespace = namespace
        self._error_map = error_map or {}

    def _call(self, name, **kwargs):
        channel = self._container.send_request(self._address, name, kwargs)
        try:
            return channel.get(timeout=self._timeout).body
        except ErrorReply as e:
            error_type = e.reply.body.get('type')
            if error_type in self._error_map:
                raise self._error_map[error_type]()
            raise

    def __getattr__(self, name):
        try:
            return self._method_cache[name]
        except KeyError:
            method = functools.partial(self._call, '%s.%s' % (self._namespace, name))
            self._method_cache[name] = method
            return method


@six.add_metaclass(InterfaceBase)
class Interface(object):
    service_type = None
    register_with_coordinator = True

    def __init__(self, container):
        self.container = container
        self.config = {}
        self.components = {}
        for declaration in self.declarations:
            declaration.install(self)

    def install(self, factory):
        self.components[factory] = factory(self)

    def apply_config(self, config):
        pass

    def configure(self, config):
        self.config.update(config)

    def handle_request(self, func_name, channel):
        self.methods[func_name](self, channel, **channel.request.body)

    def dispatch_event(self, event):
        return self.event_dispatcher(event)

    def request(self, address, subject, body, timeout=None):
        channel = self.container.send_request(address, subject, body)
        return channel.get(timeout=timeout)

    def emit(self, event_type, payload):
        self.container.emit_event(event_type, payload)

    def proxy(self, address, namespace=None, **kwargs):
        return Proxy(self.container, address, namespace=namespace, **kwargs)

    def subscribe(self, *event_types, **kwargs):
        def decorator(func):
            from lymph.core.events import EventHandler
            handler = EventHandler(func, event_types, **kwargs)
            self.container.subscribe(handler)
            return handler
        return decorator

    def on_start(self):
        for component in self.components.values():
            component.on_start()

    def on_stop(self):
        for component in self.components.values():
            component.on_stop()

    def on_connect(self, endpoint):
        pass

    def on_disconnect(self, endpoint):
        pass

    def stats(self):
        return {}


class DefaultInterface(Interface):
    service_type = 'lymph'
    register_with_coordinator = False

    @rpc()
    def ping(self, channel, payload=None):
        channel.reply(payload)

    @rpc()
    def status(self, channel):
        channel.reply({
            'endpoint': self.container.endpoint,
            'identity': self.container.identity,
            'config': self.config,
        })

    @rpc()
    def inspect(self, channel):
        """
        Returns a description of all available rpc methods of this service
        """
        methods = []
        for service_name, service in list(self.container.installed_services.items()):
            for name, func in six.iteritems(service.methods):
                args = inspect.getargspec(func)
                methods.append({
                    'name': '%s.%s' % (service_name, name),
                    'params': list(args.args[2:]),
                    'help': textwrap.dedent(func.__doc__ or '').strip(),
                })
        channel.reply({
            'methods': methods,
        })
