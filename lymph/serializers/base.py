import abc
import datetime
import decimal
import functools
import json
import uuid

import pytz
import msgpack
import six
import iso8601

from lymph.utils import Undefined


@six.add_metaclass(abc.ABCMeta)
class ExtensionTypeSerializer(object):
    @abc.abstractmethod
    def serialize(self, obj):
        raise NotImplementedError

    @abc.abstractmethod
    def deserialize(self, obj):
        raise NotImplementedError


class DatetimeSerializer(ExtensionTypeSerializer):
    format = '%Y-%m-%dT%H:%M:%S%z'

    def serialize(self, obj):
        return obj.strftime(self.format)

    def deserialize(self, obj):
        return iso8601.parse_date(obj, default_timezone=None)


class DateSerializer(ExtensionTypeSerializer):
    format = '%Y-%m-%d'

    def serialize(self, obj):
        return obj.strftime(self.format)

    def deserialize(self, obj):
        return datetime.datetime.strptime(obj, self.format).date()


class TimeSerializer(ExtensionTypeSerializer):
    format = '%H:%M:%SZ'

    def serialize(self, obj):
        return obj.strftime(self.format)

    def deserialize(self, obj):
        return datetime.datetime.strptime(obj, self.format).time()


class StrSerializer(ExtensionTypeSerializer):
    def __init__(self, factory):
        self.factory = factory

    def serialize(self, obj):
        return str(obj)

    def deserialize(self, obj):
        return self.factory(obj)


class SetSerializer(ExtensionTypeSerializer):
    def serialize(self, obj):
        return list(obj)

    def deserialize(self, obj):
        return set(obj)


class UndefinedSerializer(ExtensionTypeSerializer):
    def serialize(self, obj):
        return ''

    def deserialize(self, obj):
        return Undefined


_extension_type_serializers = {
    'datetime': DatetimeSerializer(),
    'date': DateSerializer(),
    'time': TimeSerializer(),
    'Decimal': StrSerializer(decimal.Decimal),
    'UUID': StrSerializer(uuid.UUID),
    'set': SetSerializer(),
    'UndefinedType': UndefinedSerializer(),
}


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
        elif hasattr(obj, '_lymph_dump_'):
            obj = obj._lymph_dump_()
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


EMBEDDED_MSGPACK_TYPE = 101


def raw_embed(data):
    return msgpack.ExtType(EMBEDDED_MSGPACK_TYPE, data)


def ext_hook(code, data):
    if code == EMBEDDED_MSGPACK_TYPE:
        return msgpack_serializer.loads(data)
    return msgpack.ExtType(code, data)


def _msgpack_load(stream, *args, **kwargs):
    # temporary workaround for https://github.com/msgpack/msgpack-python/pull/143
    return msgpack.loads(stream.read(), *args, **kwargs)


msgpack_serializer = BaseSerializer(
    dumps=functools.partial(msgpack.dumps, use_bin_type=True),
    loads=functools.partial(msgpack.loads, encoding='utf-8', ext_hook=ext_hook),
    dump=functools.partial(msgpack.dump, use_bin_type=True),
    load=functools.partial(_msgpack_load, encoding='utf-8', ext_hook=ext_hook),
)

json_serializer = BaseSerializer(dumps=json.dumps, loads=json.loads, dump=json.dump, load=json.load)
