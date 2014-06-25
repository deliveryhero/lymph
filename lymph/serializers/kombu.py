from __future__ import absolute_import

from kombu.serialization import BytesIO

from lymph.serializers.base import msgpack_serializer, json_serializer


def _load_msgpack(s):
    return msgpack_serializer.load(BytesIO(s))


def _load_json(s):
    return json_serializer.load(BytesIO(s))


json_serializer_args = (json_serializer.dumps, _load_json, 'application/lymph+json', 'utf-8')
msgpack_serializer_args = (msgpack_serializer.dumps, _load_msgpack, 'application/lymph+x-msgpack', 'binary')
