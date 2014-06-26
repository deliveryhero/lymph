import abc
import datetime
import decimal
import functools
import json
import msgpack
import six


@six.add_metaclass(abc.ABCMeta)
class ExtensionTypeSerializer(object):
    @abc.abstractmethod
    def serialize(self, obj):
        raise NotImplementedError

    @abc.abstractmethod
    def deserialize(self, obj):
        raise NotImplementedError


class DatetimeSerializer(ExtensionTypeSerializer):
    def __init__(self, format):
        self.format = format

    def serialize(self, obj):
        return obj.strftime(self.format)

    def deserialize(self, obj):
        return datetime.datetime.strptime(obj, self.format)


class StrSerializer(ExtensionTypeSerializer):
    def __init__(self, factory):
        self.factory = factory

    def serialize(self, obj):
        return str(obj)

    def deserialize(self, obj):
        return self.factory(obj)


class LossyTransformSerializer(ExtensionTypeSerializer):
    def __init__(self, transform):
        self.transform = transform

    def serialize(self, obj):
        return self.transform(obj)

    def deserialize(self, obj):
        return obj


_extension_type_serializers = {}

def register_serializer(t, serializer):
    name = t.__name__
    if name in _extension_type_serializers:
        raise RuntimeError('Serializer for %r already registered.' % t)
    _extension_type_serializers[name] = serializer


register_serializer(datetime.datetime, DatetimeSerializer('%Y-%m-%dT%H:%I:%SZ'))
register_serializer(datetime.date, DatetimeSerializer('%Y-%m-%d'))
register_serializer(datetime.time, DatetimeSerializer('%H:%I:%S'))
register_serializer(decimal.Decimal, StrSerializer(decimal.Decimal))
register_serializer(set, LossyTransformSerializer(list))


class BaseSerializer(object):
    def __init__(self, dumps=None, loads=None, load=None, dump=None):
        self._dumps = dumps
        self._loads = loads
        self._load = load
        self._dump = dump

    def dump_object(self, obj):
        obj_type = type(obj)
        serializer = _extension_type_serializers.get(obj_type.__name__)
        if serializer:
            obj = {
                '__type__': obj_type.__name__,
                '_': serializer.serialize(obj),
            }
        return obj

    def load_object(self, obj):
        obj_type = obj.get('__type__')
        if obj_type:
            serializer = _extension_type_serializers.get(obj_type)
            return serializer.deserialize(obj['_'])
        return obj

    def dumps(self, obj):
        return self._dumps(obj, default=self.dump_object)

    def loads(self, s):
        return self._loads(s, object_hook=self.load_object)

    def dump(self, obj, f):
        return self._dump(obj, f, default=self.dump_object)

    def load(self, f):
        return self._load(f, object_hook=self.load_object)


msgpack_serializer = BaseSerializer(
    dumps=functools.partial(msgpack.dumps, use_bin_type=True),
    loads=functools.partial(msgpack.loads, encoding='utf-8'),
    dump=functools.partial(msgpack.dump, use_bin_type=True),
    load=functools.partial(msgpack.load, encoding='utf-8'),
)

json_serializer = BaseSerializer(dumps=json.dumps, loads=json.loads, dump=json.dump, load=json.load)

