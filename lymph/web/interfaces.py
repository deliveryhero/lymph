import logging
import sys

from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import HTTPException

from lymph.core.interfaces import Interface
from lymph.core import trace
from lymph.utils.logging import setup_logger
from lymph.exceptions import SocketNotCreated
from lymph.utils.sockets import create_socket
from lymph.web.wsgi_server import LymphWSGIServer


logger = logging.getLogger(__name__)


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
        setup_logger('werkzeug')
        setup_logger('gevent')
        try:
            socket_fd = self.container.get_shared_socket_fd(self.http_port)
        except SocketNotCreated:
            socket = create_socket('%s:%s' % (self.config.get('ip') or
                                              self.container.server.ip,
                                              self.http_port),
                                   inheritable=True)
            socket_fd = socket.fileno()
        self.http_socket = create_socket('fd://%s' % socket_fd)
        self.wsgi_server = LymphWSGIServer(self.http_socket, self.application)
        self.wsgi_server.start()

    def on_stop(self):
        self.wsgi_server.stop()
        super(WebServiceInterface, self).on_stop()

    def dispatch_request(self, request):
        trace.set_id()
        logger.info('%s %s', request.method, request.path)
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
            if hasattr(e, 'to_http_response'):
                response = e.to_http_response(request.environ)
            else:
                if not self.container.debug:
                    logger.exception('uncaught exception')
                exc_info = sys.exc_info()
                extra_info = {
                    'url': request.url,
                    'trace_id': trace.get_id(),
                    'interface': self.__class__.__name__,
                }
                try:
                    self.container.error_hook(exc_info, extra=extra_info)
                except:
                    logger.exception('error hook failure')
                finally:
                    del exc_info
                if self.container.debug:
                    raise
                response = Response('', status=500)
        return response

    def get_wsgi_application(self):
        return self.application
