from __future__ import absolute_import

import logging
import six

import zmq.green as zmq

from lymph.utils.sockets import bind_zmq_socket


def get_loglevel(level_name):
    level = level_name.upper()
    if level not in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
        raise ValueError("unknown loglevel: %s" % level)
    return getattr(logging, level)


class PubLogHandler(logging.Handler):
    def __init__(self, endpoint):
        super(PubLogHandler, self).__init__()
        ctx = zmq.Context.instance()
        self.socket = ctx.socket(zmq.PUB)
        self.endpoint, port = bind_zmq_socket(self.socket, endpoint)

    def emit(self, record):
        topic = record.levelname
        self.socket.send_multipart([
            _encode(topic),
            _encode(self.endpoint),
            _encode(self.format(record))])


def _encode(potentially_text, encoding='utf-8'):
    if isinstance(potentially_text, six.text_type):
        return potentially_text.encode(encoding)
    return potentially_text
