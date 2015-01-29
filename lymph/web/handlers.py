import codecs
import json

from werkzeug.exceptions import MethodNotAllowed


http_methods = ('get', 'post', 'head', 'options', 'put', 'delete')


class RequestHandler(object):

    stream_reader = codecs.getreader("utf-8")

    def __init__(self, interface, request):
        self.request = request
        self.interface = interface
        self._json = None

    @property
    def allowed_methods(self):
        return [method.upper() for method in http_methods if callable(getattr(self, method))]

    def json(self):
        # FIXME: should we really keep a reference to the parsed body?
        if self._json is None:
            self._json = json.load(self.stream_reader(self.request.stream))
        return self._json

    def dispatch(self, args):
        method = self.request.method.lower()
        if method not in http_methods:
            raise MethodNotAllowed(self.allowed_methods)
        try:
            func = getattr(self, method)
        except AttributeError:
            raise MethodNotAllowed(self.allowed_methods)
        return func(**args)
