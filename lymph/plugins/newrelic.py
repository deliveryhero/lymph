from __future__ import absolute_import, unicode_literals

import functools

import newrelic.agent

from lymph.core import trace
from lymph.core.plugins import Plugin
from lymph.core.container import ServiceContainer
from lymph.web.interfaces import WebServiceInterface


def with_trace_id(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        newrelic.agent.add_custom_parameter('trace_id', trace.get_id())
        return func(*args, **kwargs)
    return wrapped


class NewrelicPlugin(Plugin):
    def __init__(self, container, config_file=None, environment=None, **kwargs):
        super(NewrelicPlugin, self).__init__()
        self.container = container
        self.container.error_hook.install(self.on_error)
        self.container.http_request_hook.install(self.on_http_request)
        newrelic.agent.initialize(config_file, environment)
        for method in ('send_request', 'emit_event', 'lookup'):
            setattr(ServiceContainer, method, newrelic.agent.function_trace()(getattr(ServiceContainer, method)))

    def on_interface_installation(self, interface):
        for name, method in interface.methods.items():
            method.decorate(with_trace_id)
            method.decorate(newrelic.agent.background_task())
        if isinstance(interface, WebServiceInterface):
            interface.application = newrelic.agent.wsgi_application()(interface.application)

    def on_error(self, exc_info, **kwargs):
        newrelic.agent.add_custom_parameter('trace_id', trace.get_id())
        newrelic.agent.record_exception(exc_info)

    def on_http_request(self, request, rule, kwargs):
        newrelic.agent.set_transaction_name("%s %s" % (request.method, rule))
        newrelic.agent.add_custom_parameter('trace_id', trace.get_id())
