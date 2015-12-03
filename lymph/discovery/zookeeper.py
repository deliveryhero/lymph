import functools
import json
import logging
import six

from kazoo.protocol.states import EventType, KazooState
from kazoo.handlers.gevent import SequentialGeventHandler
from kazoo.exceptions import NoNodeError, KazooException

from .base import BaseServiceRegistry, SERVICE_NAMESPACE
from lymph.exceptions import LookupFailure, RegistrationFailure
from lymph.utils.logging import setup_logger


logger = logging.getLogger(__name__)

DEFAULT_CHROOT = '/lymph'


class ZookeeperServiceRegistry(BaseServiceRegistry):
    def __init__(self, zkclient, pool=None):
        super(ZookeeperServiceRegistry, self).__init__(pool=pool)
        self.client = zkclient
        if not self.client.chroot:
            self.client.chroot = DEFAULT_CHROOT
        self.client.add_listener(self.on_kazoo_state_change)
        self.start_count = 0
        self.registered_names = {}

    @classmethod
    def from_config(cls, config, **kwargs):
        zkclient = config.get_instance('zkclient', handler=SequentialGeventHandler())
        return cls(zkclient=zkclient, **kwargs)

    def on_start(self, timeout=10):
        setup_logger('kazoo')
        self.start_count += 1
        if self.start_count > 1:
            return
        started = self.client.start_async()
        started.wait(timeout=timeout)
        if not self.client.connected:
            raise RuntimeError('could not connect to zookeeper')
        logger.debug('connected to zookeeper (version=%s)', '.'.join(map(str, self.client.server_version())))

    def on_stop(self, **kwargs):
        self.start_count -= 1
        if self.start_count != 0:
            return
        self.client.stop()

    def on_kazoo_state_change(self, state):
        logger.info('kazoo connection state changed to %s', state)
        if state == KazooState.CONNECTED:
            for (namespace, name), instance in self.registered_names.items():
                self.spawn(self.register, name, instance, namespace=namespace)
            for service in six.itervalues(self.cache):
                self.spawn(self.lookup, service, timeout=None)
        elif state == KazooState.LOST:
            logger.warning('zookeeper connection lost')
        elif state == KazooState.SUSPENDED:
            logger.info('zookeeper connection suspended')

    def on_service_name_watch(self, service, event):
        try:
            self.lookup(service)
        except LookupFailure:
            pass
        except Exception:
            logger.exception('error in service type watcher')

    def on_service_watch(self, service, event):
        try:
            prefix, service_name, instance_id = event.path.rsplit('/', 2)
            if event.type == EventType.DELETED:
                service.remove(instance_id)
        except Exception:
            logger.exception('error in service watcher')

    def _get_service_znode(self, service, service_name, instance_id):
        path = self._get_zk_path(SERVICE_NAMESPACE, service_name, instance_id)
        result = self.client.get_async(
            path, watch=functools.partial(self.on_service_watch, service))
        value, znode = result.get()
        items = six.iteritems(json.loads(value.decode('utf-8')))
        return {str(k): v for k, v in items}

    def discover(self):
        result = self.client.get_children_async(path='/%s' % SERVICE_NAMESPACE)
        try:
            return list(result.get())
        except NoNodeError:
            return []

    def lookup(self, service, timeout=1):
        if self.client.state != KazooState.CONNECTED:
            return service
        service_name = service.name
        result = self.client.get_children_async(
            path='/%s/%s' % (SERVICE_NAMESPACE, service_name, ),
            watch=functools.partial(self.on_service_name_watch, service),
        )
        try:
            instance_ids = result.get(timeout=timeout)
        except NoNodeError:
            raise LookupFailure("failed to resolve %s", service.name)
        except KazooException as e:
            logger.warning("zookeeper lookup failure: %s", e)
            return service
        logger.info("lookup %s %r", service_name, instance_ids)
        old_instance_ids = {instance.id for instance in service}
        for instance_id in instance_ids:
            kwargs = self._get_service_znode(service, service_name, instance_id)
            service.update(instance_id, **kwargs)
            try:
                old_instance_ids.remove(instance_id)
            except KeyError:
                pass
        for instance_id in old_instance_ids:
            service.remove(instance_id)
        return service

    def _get_zk_path(self, namespace, service_name, instance_id):
        return '/%s/%s/%s' % (namespace, service_name, instance_id)

    def register(self, service_name, instance, timeout=1, namespace=SERVICE_NAMESPACE):
        path = self._get_zk_path(namespace, service_name, instance.id)
        value = json.dumps(instance.serialize())

        # XXX(Mouad): In case path already exist delete it before registering,
        # this is protecting mechanism for when dev machine go to sleep or service
        # restart too fast (before zookeeper detect service is gone).
        try:
            self.client.delete(path)
        except NoNodeError:
            pass

        result = self.client.create_async(
            path,
            value.encode('utf-8'),
            ephemeral=True, makepath=True)
        # FIXME: result.set_exception(RegistrationFailure())
        result.get(timeout=timeout)
        self.registered_names[(namespace, service_name)] = instance

    def unregister(self, service_name, instance, timeout=1, namespace=SERVICE_NAMESPACE):
        path = self._get_zk_path(namespace, service_name, instance.id)
        result = self.client.delete_async(path)
        result.set_exception(RegistrationFailure())
        result.get(timeout=timeout)
        del self.registered_names[(namespace, service_name)]
