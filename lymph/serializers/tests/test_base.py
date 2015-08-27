import datetime
import decimal
import json
import unittest
import uuid

import iso8601
import pytz

from lymph.serializers import base
from lymph.serializers import msgpack_serializer, raw_embed
from lymph.utils import Undefined


class SerializerBaseTest(unittest.TestCase):
    def setUp(self):
        self.json_serializer = base.BaseSerializer(dumps=json.dumps, loads=json.loads, dump=json.dump, load=json.load)

    def assertJsonEquals(self, a, b):
        self.assertEquals(json.loads(a), b)

    def test_DatetimeSerializer_serialize(self):
        serializer = base.DatetimeSerializer()
        self.assertEqual(
            serializer.serialize(datetime.datetime(1900, 1, 1, 0, 0, 0, 1)),
            "1900-01-01T00:00:00"
        )
        self.assertEqual(
            serializer.serialize(datetime.datetime(2014, 9, 12, 8, 33, 12, 34)),
            "2014-09-12T08:33:12"
        )
        self.assertEqual(
            serializer.serialize(pytz.timezone('Europe/Berlin').localize(datetime.datetime(2014, 9, 12, 8, 33, 12))),
            "2014-09-12T08:33:12+0200"
        )

    def test_DatetimeSerializer_deserialize(self):
        serializer = base.DatetimeSerializer()
        de = serializer.deserialize("1900-01-01T00:00:00")
        self.assertEqual(serializer.deserialize("1900-01-01T00:00:00"),
                         datetime.datetime(1900, 1, 1, 0, 0))
        self.assertEqual(serializer.deserialize("2014-09-12T08:33:12"),
                         datetime.datetime(2014, 9, 12, 8, 33, 12))
        self.assertEqual(serializer.deserialize(("2014-09-12T08:33:12+0200")),
                         pytz.timezone('Europe/Berlin').localize(datetime.datetime(2014, 9, 12, 8, 33, 12)))
        with self.assertRaises(iso8601.ParseError):
            serializer.deserialize("2014-09-12T08:33:1200")
        with self.assertRaises(iso8601.ParseError):
            serializer.deserialize("2014-09-12T25:33:12")
        with self.assertRaises(iso8601.ParseError):
            serializer.deserialize("2014-02-30t08:33:12z")

    def test_DateSerializer_serialize(self):
        serializer = base.DateSerializer()
        self.assertEqual(
            serializer.serialize(datetime.date(1900, 1, 1)), "1900-01-01")
        self.assertEqual(
            serializer.serialize(datetime.date(2014, 9, 12)), "2014-09-12")

    def test_DateSerializer_deserialize(self):
        serializer = base.DateSerializer()
        self.assertEqual(serializer.deserialize("1900-01-01"),
                         datetime.date(1900, 1, 1))
        self.assertEqual(serializer.deserialize("2014-09-12"),
                         datetime.date(2014, 9, 12))
        self.assertRaises(ValueError, serializer.deserialize, "2014-02-30")

    def test_TimeSerializer_serialize(self):
        serializer = base.TimeSerializer()
        self.assertEqual(
            serializer.serialize(datetime.time(0, 0, 0, 1)), "00:00:00Z")
        self.assertEqual(
            serializer.serialize(datetime.time(8, 33, 12, 34)), "08:33:12Z")

    def test_TimeSerializer_deserialize(self):
        serializer = base.TimeSerializer()
        self.assertEqual(serializer.deserialize("00:00:00Z"),
                         datetime.time(0, 0, 0))
        self.assertEqual(serializer.deserialize("18:33:12Z"),
                         datetime.time(18, 33, 12))
        self.assertRaises(ValueError, serializer.deserialize, "25:33:12")

    def test_decimal_serialize(self):
        serializer = base.StrSerializer(decimal.Decimal)
        self.assertEqual(serializer.serialize(decimal.Decimal('3.1415')), "3.1415")
        self.assertEqual(serializer.serialize(decimal.Decimal('2.50')), "2.50")
        self.assertEqual(serializer.serialize(decimal.Decimal('NaN')), "NaN")
        self.assertEqual(serializer.serialize(decimal.Decimal('Infinity')), "Infinity")

    def test_decimal_deserialize(self):
        serializer = base.StrSerializer(decimal.Decimal)
        self.assertEqual(serializer.deserialize("3.1415"), decimal.Decimal('3.1415'))
        self.assertEqual(serializer.deserialize("2.50"), decimal.Decimal('2.50'))
        self.assertEqual(serializer.deserialize("NaN").number_class(), 'NaN')
        self.assertEqual(serializer.deserialize("Infinity"), decimal.Decimal('Infinity'))
        self.assertRaises(decimal.InvalidOperation, serializer.deserialize, "foo")

    def test_SetSerializer_serialize(self):
        serializer = base.SetSerializer()
        self.assertEqual(
            set(serializer.serialize(set(["as", "this", "is", "a", "set"]))),
            set(['this', 'a', 'as', 'set', 'is']))

    def test_SetSerializer_deserialize(self):
        serializer = base.SetSerializer()
        self.assertEqual(serializer.deserialize(["as", "this", "is", "a", "set"]),
                         set(["as", "this", "is", "a", "set"]))

    def test_BaseSerializer_dump_object(self):
        serializer = base.BaseSerializer(dumps=json.dumps, loads=json.loads, dump=json.dump, load=json.load)
        self.assertEqual(serializer.dump_object(datetime.datetime(2014, 9, 12, 8, 33, 12, 34)),
                         {'__type__': 'datetime', '_': '2014-09-12T08:33:12'})
        self.assertEqual(serializer.dump_object(datetime.date(2014, 9, 12)),
                         {'__type__': 'date', '_': '2014-09-12'})
        self.assertEqual(serializer.dump_object(decimal.Decimal('3.1415')),
                         {'__type__': 'Decimal', '_': '3.1415'})
        self.assertEqual(
            serializer.dump_object(uuid.UUID('00000000-0000-4000-8000-000000000000')),
            {'__type__': 'UUID', '_': '00000000-0000-4000-8000-000000000000'},
        )

    def test_BaseSerializer_dump(self):
        serializer = base.BaseSerializer(dumps=json.dumps, loads=json.loads, dump=json.dump, load=json.load)
        self.assertJsonEquals(
            serializer.dumps(datetime.datetime(2014, 9, 12, 8, 33, 12, 34)),
            {"__type__": "datetime", "_": "2014-09-12T08:33:12"}
        )
        self.assertJsonEquals(
            serializer.dumps(decimal.Decimal('NaN')),
            {"__type__": "Decimal", "_": "NaN"}
        )
        self.assertJsonEquals(
            serializer.dumps(set([datetime.datetime(2014, 9, 12, 8, 33, 12, 34)])),
            {"__type__": "set", "_": [{"__type__": "datetime", "_": "2014-09-12T08:33:12"}]}
        )

    def test_BaseSerializer_load_object(self):
        serializer = base.BaseSerializer(dumps=json.dumps, loads=json.loads, dump=json.dump, load=json.load)
        self.assertEqual(serializer.load_object(
                         {'__type__': 'datetime', '_': '2014-09-12T08:33:12'}),
                         datetime.datetime(2014, 9, 12, 8, 33, 12))
        self.assertEqual(serializer.load_object(
                         {'__type__': 'date', '_': '2014-09-12'}),
                         datetime.date(2014, 9, 12))
        self.assertEqual(serializer.load_object(
                         {'__type__': 'Decimal', '_': '3.1415'}),
                         decimal.Decimal('3.1415'))
        self.assertEqual(serializer.load_object(
                         {'__type__': 'Decimal', '_': 'NaN'}).number_class(),
                         'NaN')
        self.assertEqual(
            serializer.load_object({'__type__': 'set', '_': ['this', 'a', 'as', 'set', 'is']}),
            set(['this', 'a', 'as', 'set', 'is']),
        )
        self.assertEqual(
            serializer.load_object({'__type__': 'UUID', '_': '00000000-0000-4000-8000-000000000000'}),
            uuid.UUID('00000000-0000-4000-8000-000000000000'),
        )

    def test_BaseSerializer_loads(self):
        serializer = self.json_serializer
        normal_datetime = '{"__type__": "datetime", "_": "2014-09-12T08:33:12"}'
        normal_date = '{"__type__": "date", "_": "2014-09-12"}'
        number = '{"__type__": "Decimal", "_": "3.1415"}'
        nan = '{"__type__": "Decimal", "_": "NaN"}'
        some_set = '{"__type__": "set", "_": ["this", "a", "as", "set", "is"]}'

        self.assertEqual(serializer.loads(normal_datetime),
                         datetime.datetime(2014, 9, 12, 8, 33, 12))
        self.assertEqual(serializer.loads(normal_date),
                         datetime.date(2014, 9, 12))
        self.assertEqual(serializer.loads(number), decimal.Decimal('3.1415'))
        self.assertEqual(serializer.loads(nan).number_class(), 'NaN')
        self.assertEqual(serializer.loads(some_set),
                         set([u'this', u'a', u'as', u'set', u'is']))
        self.assertEqual(
            serializer.loads(
                '{"__type__": "set", "_": ['
                '{"__type__": "datetime", "_": "2014-09-12T08:33:12"}, '
                '{"__type__": "datetime", "_": "2015-09-12T08:33:12"}'
                ']}'
            ),
            {
                datetime.datetime(2014, 9, 12, 8, 33, 12),
                datetime.datetime(2015, 9, 12, 8, 33, 12)
            }
        )

    def test_undefined(self):
        self.assertJsonEquals(self.json_serializer.dumps(Undefined), {'__type__': 'UndefinedType', '_': ''})
        self.assertIs(self.json_serializer.loads('{"__type__": "UndefinedType", "_": ""}'), Undefined)


class TestRawEmbed(unittest.TestCase):
    def test_raw_is_transparent(self):
        data = {'foo': 42}
        raw_data = msgpack_serializer.dumps(data)
        packed = msgpack_serializer.dumps([raw_embed(raw_data)])
        self.assertEqual(msgpack_serializer.loads(packed), [data])
