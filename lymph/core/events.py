import functools
import re


class Event(object):
    def __init__(self, evt_type, body, source=None):
        self.evt_type = evt_type
        self.body = body
        self.source = source

    def __getitem__(self, key):
        return self.body[key]

    def __iter__(self):
        return iter(self.body)

    def __repr__(self):
        return '<Event type=%r body=%r>' % (self.evt_type, self.body)

    @classmethod
    def deserialize(cls, data):
        return cls(data.get('type'), data.get('body', {}), source=data.get('source'))

    def serialize(self):
        return {
            'type': self.evt_type,
            'body': self.body,
            'source': self.source,
        }


class EventDispatcher(object):
    wildcards = {
        '#': r'[\w.]*(?=\.|$)',
        '*': r'\w+',
    }

    def __init__(self, patterns=()):
        self.patterns = []
        self.update(patterns)

    def compile(self, key):
        words = (self.wildcards.get(word, re.escape(word)) for word in key.split('.'))
        return re.compile('^%s$' % r'\.'.join(words))

    def register(self, pattern, handler):
        self.patterns.append((
            self.compile(pattern),
            pattern,
            handler,
        ))

    def __iter__(self):
        for regex, pattern, handler in self.patterns:
            yield pattern, handler

    def update(self, other):
        for pattern, handler in other:
            self.register(pattern, handler)

    def dispatch(self, evt_type):
        for regex, pattern, handler in self.patterns:
            if regex.match(evt_type):
                yield pattern, handler

    def __call__(self, obj, event):
        handlers = set()
        for pattern, handler in self.dispatch(event.evt_type):
            if handler not in handlers:
                handlers.add(handler)
                handler(obj, event)
        return bool(handlers)

