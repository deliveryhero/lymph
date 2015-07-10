import datetime
import unittest
from lymph.utils.event_indexing import EventIndex
from lymph.core.events import Event
from mock import patch, Mock


class TestStore(unittest.TestCase):
    def setUp(self):
        def mockget(*args, **kwargs):
            return self.mocked

        def mockindex(*args, **kwargs):
            body = kwargs.get('body', {})
            self.mocked = {'_source': body}
        self.es = Mock(get=mockget, index=mockindex)

    def test_stores_event(self):
        index = EventIndex(self.es, 'index_test_name')
        event = Event('test_event', {'number': 3,
                                     'string': 'hi',
                                     'float': 3.4,
                                     'dict': {'one': 1, 'two': 'dos'},
                                     'date': datetime.date(2014, 5, 2),
                                     'bool': True,
                                     'list': [1, 2, 3]})
        with patch('uuid.uuid4', Mock(hex='testuuid')):
            index.index(event)
        es_event = self.es.get(index='index_test_name', id='testuuid')
        self.assertEquals(es_event['_source']['s_string'], 'hi')
        self.assertEquals(es_event['_source']['i_number'], 3)
        self.assertEquals(es_event['_source']['f_float'], 3.4)
        self.assertEquals(es_event['_source']['o_dict'], {'s_two': 'dos',
                                                          'i_one': 1})
        self.assertEquals(es_event['_source']['d_date'], datetime.date(
            2014, 5, 2))
        self.assertEquals(es_event['_source']['b_bool'], True)
        self.assertEquals(es_event['_source']['l_list'], [1, 2, 3])
        self.assertEquals(es_event['_source']['type'], 'test_event')
