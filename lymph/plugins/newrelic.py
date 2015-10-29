from __future__ import absolute_import, unicode_literals

import functools

import newrelic.agent

from lymph.core import trace
from lymph.core.plugins import Plugin
from lymph.core.container import ServiceContainer
from lymph.core.interfaces import ProxyMethod
from lymph.web.interfaces import WebServiceInterface


def with_trace_id(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        newrelic.agent.add_custom_parameter('trace_id', trace.get_id())
        return func(*args, **kwargs)
    return wrapped


def patch_proxy_methods():
    proxy_call = ProxyMethod.__call__

    @functools.wraps(proxy_call)
    def wrapped_proxy_call(self, **kwargs):
        transaction = newrelic.agent.current_transaction()
        with newrelic.agent.FunctionTrace(transaction, name=self.subject, group='Python/RPC'):
            return proxy_call(self, **kwargs)
    ProxyMethod.__call__ = wrapped_proxy_call


class NewrelicPlugin(Plugin):
    def __init__(self, container, config_file=None, environment=None, **kwargs):
        super(NewrelicPlugin, self).__init__()
        self.container = container
        self.container.error_hook.install(self.on_error)
        self.container.http_request_hook.install(self.on_http_request)
        newrelic.agent.initialize(config_file, environment)
        patch_proxy_methods()

    def on_interface_installation(self, interface):
        self._wrap_methods(interface.methods)
        self._wrap_methods(interface.event_handlers)
        if isinstance(interface, WebServiceInterface):
            interface.application = newrelic.agent.wsgi_application()(interface.application)

    def _wrap_methods(self, methods):
        for name, method in methods.items():
            method.decorate(with_trace_id)
            method.decorate(newrelic.agent.background_task())

    def on_error(self, exc_info, **kwargs):
        newrelic.agent.add_custom_parameter('trace_id', trace.get_id())
        newrelic.agent.record_exception(exc_info)

    def on_http_request(self, request, rule, kwargs):
        newrelic.agent.set_transaction_name("%s %s" % (request.method, rule))
        newrelic.agent.add_custom_parameter('trace_id', trace.get_id())
