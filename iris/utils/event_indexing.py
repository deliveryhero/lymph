from __future__ import absolute_import
from datetime import (date, datetime)
import logging
import six
import uuid


logger = logging.getLogger(__name__)


class EventIndex(object):
    def __init__(self, es, index_name='events'):
        self.es = es
        self.index_name = index_name

    def prepare_object(self, data):
        return dict(self.prepare_value(key, value)
                    for key, value in six.iteritems(data))

    def prepare_value(self, key, value):
        if isinstance(value, six.integer_types):
            type_prefix = 'i'
        elif isinstance(value, six.string_types):
            type_prefix = 's'
        elif isinstance(value, float):
            type_prefix = 'f'
        elif isinstance(value, dict):
            type_prefix = 'o'
            value = self.prepare_object(value)
        elif isinstance(value, (datetime, date)):
            type_prefix = 'd'
        elif isinstance(value, bool):
            type_prefix = 'b'
        else:
            raise TypeError('cannot index values of type %s' % type(value))
        return ('%s_%s' % (type_prefix, key)), value

    def index(self, event, index_name=None):
        event_id = uuid.uuid4().hex
        body = self.prepare_object(event.body)
        body.update({
            'type': event.evt_type,
            'source': event.source,
            'logged_at': datetime.utcnow(),
        })
        self.es.index(
            index=index_name or self.index_name,
            doc_type='event',
            id=event_id,
            body=body,
        )


class DatedEventIndex(EventIndex):
    def create_index_alias(self):
        if self.es.indices.exists_alias(self.index_name):
            logger.info('index alias already exists')
        self.es.indices.put_alias(
            index='%s-*' % self.index_name,
            name=self.index_name,
        )

    def get_index_name(self, dt):
        return '%s-%s' % (self.index_name, dt.strftime('%Y.%m.%d'))

    def index(self, event, index_name=None):
        super('DatedEventIndex', self).index(event, self.get_index_name(
            datetime.now()))

