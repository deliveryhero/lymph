from __future__ import absolute_import

import newrelic.agent

from lymph.core.plugins import Plugin
from lymph.web.interfaces import WebServiceInterface


class NewrelicPlugin(Plugin):
    def __init__(self, container, config_file=None, environment=None, **kwargs):
        super(NewrelicPlugin, self).__init__()
        self.container = container
        self.container.error_hook.install(self.on_error)
        newrelic.agent.initialize(config_file, environment)

    def on_interface_installation(self, interface):
        for name, method in interface.methods.items():
            method.decorate(newrelic.agent.background_task())
        if isinstance(interface, WebServiceInterface):
            interface.application = newrelic.agent.wsgi_application()(interface.application)

    def on_error(self, exc_info, **kwargs):
        newrelic.agent.record_exception(exc_info)

