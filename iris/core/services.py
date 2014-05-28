import hashlib
import logging
import random
import six

logger = logging.getLogger(__name__)


class ServiceInstance(object):
    def __init__(self, container, endpoint=None, identity=None, **info):
        self.container = container
        self.identity = identity if identity else hashlib.md5(endpoint.encode('utf-8')).hexdigest()
        self.update(endpoint, **info)
        self.connection = None

    def update(self, endpoint, log_endpoint=None, service_type=None):
        self.endpoint = endpoint
        self.log_endpoint = log_endpoint
        self.service_type = service_type

    def connect(self):
        self.connection = self.container.connect(self.endpoint)
        return self.connection

    def disconnect(self):
        if self.connection:
            self.container.disconnect(self.endpoint)
            self.connection = None

    def is_alive(self):
        return self.connection is None or self.connection.is_alive()


class Service(object):
    def __init__(self, container, service_type=None, instances=()):
        self.container = container
        self.service_type = service_type
        self.instances = {i.endpoint: i for i in instances}

    def __iter__(self):
        return six.itervalues(self.instances)

    def __len__(self):
        return len(self.instances)

    def identities(self):
        return list(self.instances.keys())

    def connect(self):
        choices = [i for i in self if i.is_alive()]
        if not choices:
            logger.info("no live instance for %s", self.service_type)
            choices = list(self.instances.values())
        instance = random.choice(choices)
        return instance.connect()

    def disconnect(self):
        for instance in self:
            instance.disconnect()

    def remove(self, identity):
        try:
            instance = self.instances.pop(identity)
        except KeyError:
            pass
        else:
            instance.disconnect()

    def update(self, identity, **info):
        if identity in self.instances:
            self.instances[identity].update(**info)
        else:
            self.instances[identity] = ServiceInstance(self.container, **info)
