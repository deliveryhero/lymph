import collections


class RawMetric(object):

    def __init__(self, name, value, tags=None):
        self._name = name
        self._value = value
        self._tags = tags or {}

    def __iter__(self):
        yield (self._name, self._value, self._tags)

    def __repr__(self):
        return '%s(name=%r, value=%r, tags=%r)' % (
            self.__class__.__name__,
            self._name,
            self._value,
            self._tags)

    __str__ = __repr__


class Counter(RawMetric):

    def __init__(self, name, tags=None):
        super(Counter, self).__init__(name, 0, tags)

    def __iadd__(self, value):
        self._value += value
        return self


class TaggedCounter(RawMetric):

    def __init__(self, name, tags=None):
        super(TaggedCounter, self).__init__(name, collections.Counter(), tags)

    def incr(self, _value=1, **tags):
        tags.update(self._tags)
        self._value[frozenset(tags.items())] += _value

    def __iter__(self):
        for tags, count in self._value.items():
            yield self._name, count, dict(tags)
