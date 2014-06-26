import logging

from lymph.core.interfaces import Interface
from lymph.core.decorators import rpc


logger = logging.getLogger(__name__)


class Coordinator(Interface):
    service_type = 'coordinator'
    register_with_coordinator = False

    def __init__(self, *args, **kwargs):
        super(Coordinator, self).__init__(*args, **kwargs)
        self.service_map = {}
        self.endpoint_map = {}
        self.watchers = {}

    def on_disconnect(self, endpoint):
        if endpoint not in self.endpoint_map:
            return
        logger.info("coordinator disconnect %s", endpoint)
        service_type = self.endpoint_map[endpoint]
        services = self.service_map.get(service_type, [])
        self.service_map[service_type] = [s for s in services if s['endpoint'] != endpoint]

    @rpc()
    def register(self, channel, service_type=None, endpoint=None, log_endpoint=None, identity=None):
        # FIXME: complain if service_type is None
        services = self.service_map.setdefault(service_type, [])
        msg = channel.request
        self.endpoint_map[endpoint] = service_type
        info = msg.body.copy()
        info['endpoint'] = msg.source
        services.append({
            'endpoint': endpoint,
            'log_endpoint': log_endpoint,
            'identity': identity,
        })
        logger.info('registered service %r', info)
        channel.reply({})
        for watcher in self.watchers.get(service_type, ()):
            self.request(watcher, 'lymph.notice', dict(service_type=service_type, instances=services))

    @rpc()
    def lookup(self, channel, service_type=None, watch=True):
        channel.reply(self.service_map.get(service_type, []))
        if watch:
            watchers = self.watchers.setdefault(service_type, set())
            watchers.add(channel.request.source)

    @rpc()
    def discover(self, channel):
        channel.reply(list(self.service_map.keys()))
