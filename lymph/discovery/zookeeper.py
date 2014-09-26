import functools
import json
import logging
import six

from kazoo.client import KazooClient
from kazoo.protocol.states import EventType, KazooState
from kazoo.handlers.gevent import SequentialGeventHandler
from kazoo.exceptions import NoNodeError, ConnectionLoss

from .base import BaseServiceRegistry
from lymph.exceptions import LookupFailure, RegistrationFailure


logger = logging.getLogger(__name__)

DEFAULT_HOSTS = '127.0.0.1:2181'
DEFAULT_CHROOT = '/lymph'


class ZookeeperServiceRegistry(BaseServiceRegistry):
    def __init__(self, hosts=DEFAULT_HOSTS, chroot=DEFAULT_CHROOT):
        super(ZookeeperServiceRegistry, self).__init__()
        self.chroot = chroot
        self.client = KazooClient(
            hosts=hosts,
            handler=SequentialGeventHandler(),
        )
        self.client.add_listener(self.on_kazoo_state_change)
        self.start_count = 0

    @classmethod
    def from_config(cls, config, **kwargs):
        return cls(
            hosts=config.get('hosts', DEFAULT_HOSTS),
            chroot=config.get('chroot', DEFAULT_CHROOT),
            **kwargs
        )

    def on_start(self, timeout=10):
        self.start_count += 1
        if self.start_count > 1:
            return
        started = self.client.start_async()
        started.wait(timeout=timeout)
        if not self.client.connected:
            raise RuntimeError('could not connect to zookeeper')
        logger.debug('connected to zookeeper (version=%s)', '.'.join(map(str, self.client.server_version())))

    def on_stop(self):
        self.start_count -= 1
        if self.start_count != 0:
            return
        self.client.stop()

    def on_kazoo_state_change(self, state):
        logger.info('kazoo connection state changed to %s', state)
        if state == KazooState.CONNECTED:
            for service in six.itervalues(self.cache):
                self.container.spawn(self.lookup, service, timeout=None)

    def on_service_type_watch(self, service, event):
        try:
            self.lookup(service)
        except LookupFailure:
            pass
        except Exception:
            logger.exception('error in service type watcher')

    def on_service_watch(self, service, event):
        try:
            prefix, service_type, identity = event.path.rsplit('/', 2)
            if event.type == EventType.DELETED:
                service.remove(identity)
        except Exception:
            logger.exception('error in service watcher')

    def _get_service_znode(self, service, service_type, identity):
        path = self._get_zk_path(service_type, identity)
        result = self.client.get_async(
            path, watch=functools.partial(self.on_service_watch, service))
        value, znode = result.get()
        items = six.iteritems(json.loads(value.decode('utf-8')))
        return {str(k): str(v) for k, v in items}

    def discover(self):
        result = self.client.get_children_async(
            path='%s/services' % self.chroot,
        )
        try:
            return list(result.get())
        except NoNodeError:
            return []

    def lookup(self, service, watch=True, timeout=1):
        service_type = service.service_type
        result = self.client.get_children_async(
            path='%s/services/%s' % (self.chroot, service_type),
            watch=functools.partial(self.on_service_type_watch, service),
        )
        try:
            names = result.get(timeout=timeout)
        except NoNodeError:
            raise LookupFailure(None, "failed to resolve %s" % service.service_type)
        except ConnectionLoss:
            logger.warning("lost zookeeper connection")
            return service
        logger.info("lookup %s %r", service_type, names)
        identities = set(service.identities())
        for name in names:
            kwargs = self._get_service_znode(service, service_type, name)
            identity = kwargs.pop('identity')
            service.update(identity, **kwargs)
            try:
                identities.remove(identity)
            except KeyError:
                pass
        for identity in identities:
            service.remove(identity)
        return service

    def _get_zk_path(self, service_type, identity):
        return '%s/services/%s/%s' % (self.chroot, service_type, identity)

    def register(self, service_type, timeout=1):
        path = self._get_zk_path(service_type, self.container.identity)
        value = json.dumps(self.container.get_instance_description())
        result = self.client.create_async(
            path,
            value.encode('utf-8'),
            ephemeral=True, makepath=True)
        # FIXME: result.set_exception(RegistrationFailure())
        result.get(timeout=timeout)

    def unregister(self, service_type, timeout=1):
        path = self._get_zk_path(service_type, self.container.identity)
        result = self.client.delete_async(path)
        result.set_exception(RegistrationFailure())
        result.get(timeout=timeout)
