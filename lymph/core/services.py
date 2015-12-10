from __future__ import unicode_literals
import abc
import logging

import six
import semantic_version

from lymph.utils import observables, hash_id
from lymph.core.versioning import compatible, serialize_version


logger = logging.getLogger(__name__)

# Event types propagated by Service when instances change.
ADDED = 'ADDED'
REMOVED = 'REMOVED'
UPDATED = 'UPDATED'


class ServiceInstance(object):
    def __init__(self, id=None, identity=None, **info):
        self.id = id
        self.identity = identity if identity else hash_id(info.get('endpoint'))
        self.info = {}
        self.update(**info)

    def update(self, **info):
        version = info.pop('version', None)
        if version:
            version = semantic_version.Version(version)
        self.version = version
        self.info.update(info)

    def __getattr__(self, name):
        try:
            return self.info[name]
        except KeyError:
            raise AttributeError(name)

    def serialize(self):
        d = {
            'id': self.id,
            'identity': self.identity,
            'version': serialize_version(self.version),
        }
        d.update(self.info)
        return d


@six.add_metaclass(abc.ABCMeta)
class InstanceSet(observables.Observable):
    @abc.abstractmethod
    def __iter__(self):
        raise NotImplementedError()

    def match_version(self, version):
        return VersionedServiceView(self, version)


class Service(InstanceSet):
    def __init__(self, name=None, instances=()):
        super(Service, self).__init__()
        self.name = name
        self.instances = {i.id: i for i in instances}
        self.version = None

    def __str__(self):
        return self.name

    def __iter__(self):
        return six.itervalues(self.instances)

    def __len__(self):
        return len(self.instances)

    def get_instance(self, prefix):
        for instance in six.itervalues(self.instances):
            if instance.id.startswith(prefix):
                return instance

    def identities(self):
        return list(self.instances.keys())

    def remove(self, instance_id):
        try:
            instance = self.instances.pop(instance_id)
        except KeyError:
            pass
        else:
            self.notify_observers(REMOVED, instance)

    def update(self, instance_id, **info):
        try:
            instance = self.instances[instance_id]
        except KeyError:
            instance = self.instances[instance_id] = ServiceInstance(**info)
            self.notify_observers(ADDED, instance)
        else:
            instance.update(**info)
            self.notify_observers(UPDATED, instance)


class VersionedServiceView(InstanceSet):
    def __init__(self, service, version):
        self.service = service
        self.spec = compatible(version)
        self.version = version

    def __str__(self):
        return '%s@%s' % (self.name, self.version)

    @property
    def name(self):
        return self.service.name

    def __iter__(self):
        for instance in self.service:
            if instance.version in self.spec:
                yield instance

    def observe(self, *args, **kwargs):
        return self.service.observe(*args, **kwargs)
