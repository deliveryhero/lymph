import hashlib
import logging

import six

from lymph.utils import observables


logger = logging.getLogger(__name__)

# Event types propagated by Service when instances change.
ADDED = 'ADDED'
REMOVED = 'REMOVED'
UPDATED = 'UPDATED'


class ServiceInstance(object):
    def __init__(self, endpoint=None, identity=None, **info):
        self.identity = identity if identity else hashlib.md5(endpoint.encode('utf-8')).hexdigest()
        self.info = info
        self.update(endpoint, **info)

    def update(self, endpoint, **info):
        self.endpoint = endpoint
        self.__dict__.update(info)
        self.info.update(info)

    def serialize(self):
        d = {
            'endpoint': self.endpoint,
            'identity': self.identity,
            'log_endpoint': self.log_endpoint,
            'fqdn': self.fqdn,
        }
        d.update(self.info)
        return d


class Service(observables.Observable):
    def __init__(self, name=None, instances=()):
        super(Service, self).__init__()
        self.name = name
        self.instances = {i.endpoint: i for i in instances}

    def __iter__(self):
        return six.itervalues(self.instances)

    def __len__(self):
        return len(self.instances)

    def get_instance(self, identity_prefix):
        for instance in six.itervalues(self.instances):
            if instance.identity.startswith(identity_prefix):
                return instance

    def identities(self):
        return list(self.instances.keys())

    def remove(self, identity):
        try:
            instance = self.instances.pop(identity)
        except KeyError:
            pass
        else:
            self.notify_observers(REMOVED, instance)

    def update(self, identity, **info):
        if identity in self.instances:
            self.instances[identity].update(**info)
            self.notify_observers(UPDATED, self.instances[identity])
        else:
            instance = self.instances[identity] = ServiceInstance(**info)
            self.notify_observers(ADDED, instance)
