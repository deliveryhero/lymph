from raven import Client

from lymph.core.plugins import Plugin


class SentryPlugin(Plugin):
    def __init__(self, container, dsn=None, **kwargs):
        super(SentryPlugin, self).__init__()
        self.container = container
        self.client = Client(dsn)
        self.container.error_hook.install(self.on_error)

    def on_error(self, exc_info, **kwargs):
        self.client.captureException(exc_info, **kwargs)
