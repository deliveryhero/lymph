import abc
import six


class Metrics(object):
    def __init__(self, **tags):
        self.__metrics = []
        self.tags = tags

    def add(self, metric):
        self.__metrics.append(metric)

    def add_tags(self, **tags):
        self.tags.update(tags)

    def __call__(self):
        return iter(self)

    def __iter__(self):
        for metrics in self.__metrics:
            for name, value, tags in metrics():
                tags.update(self.tags)
                yield name, value, tags

    def __repr__(self):
        return '<%s tags=%r metrics=%r>' % (self.__class__.__name__, self.tags, self.__metrics)
