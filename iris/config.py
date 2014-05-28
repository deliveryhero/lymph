import six
import yaml
from iris.utils import import_object


class Configuration(object):
    def __init__(self, values=None):
        self.values = values or {}

    def load_file(self, filename, sections=None):
        with open(filename, 'r') as f:
            self.load(f, sections=sections)

    def load(self, f, sections=None):
        for section, values in six.iteritems(yaml.load(f)):
            if sections is None or section in sections:
                self.values[section] = values

    def update(self, data):
        self.values.update(data)

    def set(self, key, data):
        path = key.split('.')
        values = self.values
        for bit in path[:-1]:
            new_values = values.setdefault(bit, {})
            if new_values is None:
                values[bit] = {}
                values = values[bit]
            else:
                values = new_values
        values[path[-1]] = data

    def setdefault(self, key, default):
        value = self.get(key)
        if value is None:
            self.set(key, default)
            return default
        return value

    def create_instance(self, key, default_class=None, **kwargs):
        config = self.get(key, {})
        path = config.pop('class', default_class)
        cls = import_object(path)
        return cls.from_config(config, **kwargs)

    def get(self, key, default=None):
        path = key.split('.')
        values = self.values
        for bit in path[:-1]:
            try:
                values = values[bit]
            except KeyError:
                return default
            if values is None:
                return default
        return values.get(path[-1], default)

    def __repr__(self):
        return "iris.config.Configuration(values={values})".format(
            values=self.values)
