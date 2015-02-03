import codecs
import json

from werkzeug.exceptions import MethodNotAllowed


http_methods = ('get', 'post', 'head', 'options', 'put', 'delete')


class RequestHandler(object):

    def __init__(self, interface, request):
        self.request = request
        self.interface = interface
        self._json = None

    @property
    def allowed_methods(self):
        return [method.upper() for method in http_methods if callable(getattr(self, method))]

    def json(self):
        # FIXME: should we really keep a reference to the parsed body?
        request_is_json = "application/json" == self.request.mimetype
        if request_is_json and self._json is None:
            reader = codecs.getreader(self.request.charset)
            self._json = json.load(reader(self.request.stream))
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
