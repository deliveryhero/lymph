import inspect
import textwrap
import functools
import six

from iris.core.decorators import rpc
from iris.core.events import EventDispatcher
from iris.exceptions import ErrorReply


class InterfaceBase(type):
    def __new__(cls, clsname, bases, attrs):
        methods = {}
        event_dispatcher = EventDispatcher()
        for base in bases:
            if isinstance(base, InterfaceBase):
                methods.update(base.methods)
                event_dispatcher.update(base.event_dispatcher)
        for name, value in six.iteritems(attrs):
            if callable(value):
                if getattr(value, '_rpc', False):
                    methods[name] = value
                for event_type in getattr(value, '_event_types', ()):
                    event_dispatcher.register(event_type, value)
        attrs.setdefault('service_type', clsname.lower())
        new_cls = super(InterfaceBase, cls).__new__(cls, clsname, bases, attrs)
        new_cls.methods = methods
        new_cls.event_dispatcher = event_dispatcher
        return new_cls


class Proxy(object):
    def __init__(self, container, address, timeout=1, namespace='', error_map=None):
        self._container = container
        self._address = address
        self._method_cache = {}
        self._timeout = timeout
        if address.startswith('iris://') and not namespace:
            namespace = address[7:]
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

    def on_start(self):
        pass

    def on_stop(self):
        pass

    def on_connect(self, endpoint):
        pass

    def on_disconnect(self, endpoint):
        pass

    def stats(self):
        return {}


class DefaultInterface(Interface):
    service_type = 'iris'
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
