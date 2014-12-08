import sys
import logging

from gevent.pywsgi import WSGIServer
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import HTTPException

from lymph.core.interfaces import Interface
from lymph.core import trace
from lymph.exceptions import SocketNotCreated
from lymph.utils.sockets import create_socket


logger = logging.getLogger(__name__)


# XXX(Mouad): Workaround to log correctly in gevent wsgi.
# https://github.com/gevent/gevent/issues/106
class _LoggerStream(object):

    def write(self, msg):
        logger.info(msg)


class WebServiceInterface(Interface):
    http_port = 80

    def __init__(self, *args, **kwargs):
        super(WebServiceInterface, self).__init__(*args, **kwargs)
        self.application = Request.application(self.dispatch_request)
        if self.container.debug:
            from werkzeug.debug import DebuggedApplication
            self.application = DebuggedApplication(self.application, evalex=True)
        self.wsgi_server = None

    def __call__(self, *args, **kwargs):
        # Make the object itself a WSGI app
        return self.application(*args, **kwargs)

    def on_start(self):
        super(WebServiceInterface, self).on_start()
        try:
            socket_fd = self.container.get_shared_socket_fd(self.http_port)
        except SocketNotCreated:
            socket = create_socket('%s:%s' % (self.config.get('ip') or
                                              self.container.ip,
                                              self.http_port),
                                   inheritable=True)
            socket_fd = socket.fileno()
        self.http_socket = create_socket('fd://%s' % socket_fd)
        self.wsgi_server = WSGIServer(self.http_socket, self.application, log=_LoggerStream())
        self.wsgi_server.start()

    def on_stop(self):
        self.wsgi_server.stop()
        super(WebServiceInterface, self).on_stop()

    def dispatch_request(self, request):
        trace.set_id()
        urls = self.url_map.bind_to_environ(request.environ)
        request.urls = urls
        try:
            endpoint, args = urls.match()
            if callable(endpoint):
                handler = endpoint(self, request)
                response = handler.dispatch(args)
            else:
                try:
                    handler = getattr(self, endpoint)
                except AttributeError:
                    raise  # FIXME
                response = handler(request, **args)
        except HTTPException as e:
            response = e.get_response(request.environ)
        except Exception as e:
            if not self.container.debug:
                logger.exception('uncaught exception')
            exc_info = sys.exc_info()
            try:
                self.container.error_hook(exc_info)
            except:
                logger.exception('error hook failure')
            finally:
                del exc_info
            if self.container.debug:
                raise
            return Response('', state=500)
        return response

    def get_wsgi_application(self):
        return self.application
