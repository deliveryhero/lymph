import logging

from gevent.pywsgi import WSGIServer, WSGIHandler


logger = logging.getLogger(__name__)


class LymphWSGIHandler(WSGIHandler):

    def format_request(self):
        # XXX(Mouad): Copied shamessly from gevent.pywsgi.WSGIHandler's format_request
        # and removed only the datetime from the output, since it's already part of
        # lymph logger format.
        length = self.response_length or '-'
        if self.time_finish:
            delta = '%f' % (self.time_finish - self.time_start)
        else:
            delta = '-'
        client_address = self.client_address[0] if isinstance(self.client_address, tuple) else self.client_address
        return 'client=%s - - "%s" status=%s length=%s duration=%s (seconds)' % (
            client_address or '-',
            getattr(self, 'requestline', ''),
            (getattr(self, 'status', None) or '000').split()[0],
            length,
            delta)

    def log_request(self):
        # XXX(Mouad): Workaround to log correctly in gevent wsgi.
        # https://github.com/gevent/gevent/issues/106
        logger.info(self.format_request())


class LymphWSGIServer(WSGIServer):
    handler_class = LymphWSGIHandler
