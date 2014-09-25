from lymph.serializers import msgpack_serializer
from lymph.utils import make_id


class Message(object):
    ACK = b'ACK'
    REP = b'REP'
    REQ = b'REQ'
    NACK = b'NACK'
    ERROR = b'ERROR'

    def __init__(self, msg_type, subject, packed_body=None, headers=None, packed_headers=None, msg_id=None, source=None, lazy=False, **kwargs):
        self.id = msg_id if msg_id else make_id()
        self.type = msg_type
        self.subject = subject
        self.source = source

        if headers and packed_headers:
            raise TypeError("Message takes either 'headers' or 'packed_headers' not both")
        elif not headers and not packed_headers:
            headers = {}
        self._headers = headers
        self._packed_headers = packed_headers

        if 'body' in kwargs:
            if packed_body is not None:
                raise TypeError("Message takes either 'body' or 'packed_body' not both")
            self._body = kwargs['body']
        elif packed_body is None:
            raise TypeError("Message requires either 'body' or 'packed_body'")

        self._packed_body = packed_body
        if not lazy:
            self.body
            self.packed_body
            self.headers
            self.packed_headers

    def is_request(self):
        return self.type == self.REQ

    def is_reply(self):
        return self.type in (self.REP, self.ACK, self.NACK, self.ERROR)

    def is_idle_chatter(self):
        return not self.is_request() or self.subject == '_ping'

    @property
    def body(self):
        if not hasattr(self, '_body'):
            self._body = msgpack_serializer.loads(self._packed_body)
        return self._body

    @property
    def packed_body(self):
        if self._packed_body is None:
            self._packed_body = msgpack_serializer.dumps(self._body)
        return self._packed_body

    @property
    def headers(self):
        if self._headers is None:
            self._headers = msgpack_serializer.loads(self._packed_headers)
        return self._headers

    @property
    def packed_headers(self):
        if self._packed_headers is None:
            self._packed_headers = msgpack_serializer.dumps(self._headers)
        return self._packed_headers

    def pack_frames(self):
        return [
            self.id.encode('utf-8'),
            self.type,
            self.subject.encode('utf-8'),
            self.packed_headers,
            self.packed_body,
        ]

    @classmethod
    def unpack_frames(self, frames):
        try:
            source, msg_id, msg_type, subject, headers, body = frames
        except ValueError:
            raise ValueError('bad message frame count: got %s, expected 6' % len(frames))

        try:
            msg_id = msg_id.decode('utf-8')
            subject = subject.decode('utf-8')
            source = source.decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError('message id, subject, and source must be utf-8 encoded.')

        return Message(
            msg_type=msg_type,
            subject=subject,
            msg_id=msg_id,
            source=source,
            packed_body=body,
            packed_headers=headers,
        )

    def __str__(self):
        return '{type=%s subject=%s id=%s..}' % (
            self.type,
            self.subject,
            self.id[:10],
        )

    def __repr__(self):
        return '<Message id=%s type=%s subject=%s body=%r>' % (
            self.id,
            self.type,
            self.subject,
            self.body,
        )
