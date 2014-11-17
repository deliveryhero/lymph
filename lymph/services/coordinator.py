import logging

from lymph.core.interfaces import Interface
from lymph.core.decorators import raw_rpc, rpc


logger = logging.getLogger(__name__)


class Coordinator(Interface):
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
        service_name = self.endpoint_map[endpoint]
        services = self.service_map.get(service_name, [])
        self.service_map[service_name] = [s for s in services if s['endpoint'] != endpoint]

    @raw_rpc()
    def register(self, channel, service_name=None, endpoint=None, log_endpoint=None, identity=None):
        # FIXME: complain if service_name is None
        services = self.service_map.setdefault(service_name, [])
        msg = channel.request
        self.endpoint_map[endpoint] = service_name
        info = msg.body.copy()
        info['endpoint'] = msg.source
        services.append({
            'endpoint': endpoint,
            'log_endpoint': log_endpoint,
            'identity': identity,
        })
        logger.info('registered service %r', info)
        channel.reply({})
        for watcher in self.watchers.get(service_name, ()):
            self.request(watcher, 'lymph.notice', dict(service_name=service_name, instances=services))

    @raw_rpc()
    def lookup(self, channel, service_name=None, watch=True):
        channel.reply(self.service_map.get(service_name, []))
        if watch:
            watchers = self.watchers.setdefault(service_name, set())
            watchers.add(channel.request.source)

    @rpc()
    def discover(self):
        return list(self.service_map.keys())
