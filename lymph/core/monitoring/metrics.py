import abc
import collections
import six


@six.add_metaclass(abc.ABCMeta)
class Metric(object):
    def __init__(self, name, tags=None):
        self._name = name
        self._tags = tags or {}

    @abc.abstractmethod
    def __iter__(self):
        raise NotImplementedError()

    def __repr__(self):
        return '%s(name=%r, tags=%r)' % (
            self.__class__.__name__,
            self._name,
            self._tags,
        )

    __str__ = __repr__


class Callable(Metric):
    def __init__(self, name, func, tags=None):
        super(Callable, self).__init__(name, tags)
        self.func = func

    def __iter__(self):
        yield (self._name, self.func(), self._tags)


class Gauge(Metric):
    def __init__(self, name, value=0, tags=None):
        super(Gauge, self).__init__(name, tags)
        self.value = value

    def set(self, value):
        self.value = value

    def __iter__(self):
        yield self._name, self.value, self._tags


class Generator(object):
    def __init__(self, func):
        self.func = func

    def __iter__(self):
        return self.func()


class Aggregate(object):
    def __init__(self, metrics=(), tags=None):
        self._metrics = list(metrics)
        self._tags = tags or {}

    def add(self, metric):
        self._metrics.append(metric)
        return metric

    def add_tags(self, **tags):
        self._tags.update(tags)

    def __iter__(self):
        for metric in self._metrics:
            for name, value, tags in metric:
                tags.update(self._tags)
                yield name, value, tags


class Counter(Metric):
    def __init__(self, name, tags=None):
        super(Counter, self).__init__(name, tags)
        self._value = 0

    def __iadd__(self, value):
        self._value += value
        return self

    def __iter__(self):
        yield self._name, self._value, self._tags


class TaggedCounter(Metric):
    def __init__(self, name, tags=None):
        super(TaggedCounter, self).__init__(name, tags)
        self._values = collections.Counter()

    def incr(self, _by=1, **tags):
        tags.update(self._tags)
        self._values[frozenset(tags.items())] += _by

    def __iter__(self):
        for tags, count in six.iteritems(self._values):
            yield self._name, count, dict(tags)
