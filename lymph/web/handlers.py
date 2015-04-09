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
        return [method.upper() for method in http_methods if callable(getattr(self, method, None))]

    def json(self):
        if not "application/json" == self.request.mimetype:
            raise ValueError("The request Content-Type is not JSON")

        if self._json is None:
            self._json = json.loads(self.request.get_data(as_text=True))
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
