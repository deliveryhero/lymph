from __future__ import absolute_import
import logging
from logging.config import dictConfig

import six
import zmq.green as zmq

from lymph.utils.sockets import bind_zmq_socket


def get_loglevel(level_name):
    level = level_name.upper()
    if level not in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
        raise ValueError("unknown loglevel: %s" % level)
    return getattr(logging, level)


def setup_logger(name):
    """Setup and return logger ``name`` with same settings as 'lymph' logger."""
    lymph_logger = logging.getLogger('lymph')
    logger = logging.getLogger(name)
    for hdlr in lymph_logger.handlers:
        logger.addHandler(hdlr)
    logger.setLevel(lymph_logger.level)
    return logger


class PubLogHandler(logging.Handler):
    def __init__(self, endpoint):
        super(PubLogHandler, self).__init__()
        ctx = zmq.Context.instance()
        self.socket = ctx.socket(zmq.PUB)
        self.endpoint, port = bind_zmq_socket(self.socket, endpoint)

    def emit(self, record):
        topic = record.levelname
        self.socket.send_multipart([
            self._encode(topic),
            self._encode(self.endpoint),
            self._encode(self.format(record))])

    @staticmethod
    def _encode(potentially_text, encoding='utf-8'):
        if isinstance(potentially_text, six.text_type):
            return potentially_text.encode(encoding)
        return potentially_text


def setup_logging(logconf, loglevel, logfile, log_endpoint):
    logconf.setdefault('version', 1)
    formatters = logconf.setdefault('formatters', {})
    formatters.setdefault('_trace', {
        '()': 'lymph.core.trace.TraceFormatter',
        'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s - (trace-id:%(trace_id)s)',
    })
    handlers = logconf.setdefault('handlers', {})
    handlers.setdefault('_zmqpub', {
        'class': 'lymph.utils.logging.PubLogHandler',
        'formatter': '_trace',
        'endpoint': log_endpoint,
    })
    console_logconf = {
        'class': 'logging.StreamHandler',
        'formatter': '_trace',
        'level': loglevel.upper(),
    }
    if logfile:
        console_logconf.update({
            'class': 'logging.FileHandler',
            'filename': logfile
        })
    handlers.setdefault('_console', console_logconf)
    loggers = logconf.setdefault('loggers', {})
    loggers.setdefault('lymph', {
        'handlers': ['_console', '_zmqpub'],
        'level': 'DEBUG',
    })
    dictConfig(logconf)
