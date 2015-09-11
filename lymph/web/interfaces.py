import logging
import sys

from werkzeug.contrib.wrappers import DynamicCharsetRequestMixin
from werkzeug.wrappers import Request as BaseRequest, Response
from werkzeug.exceptions import HTTPException, NotFound, MethodNotAllowed

from lymph.core.interfaces import Interface
from lymph.core import trace
from lymph.utils.logging import setup_logger
from lymph.exceptions import SocketNotCreated, NoSharedSockets
from lymph.utils import sockets
from lymph.core.trace import Group
from lymph.web.wsgi_server import LymphWSGIServer
from lymph.web.routing import HandledRule


logger = logging.getLogger(__name__)


class Request(DynamicCharsetRequestMixin, BaseRequest):
    default_charset = 'utf-8'

    @property
    def full_path(self):
        full_path = super(Request, self).full_path
        return full_path.rstrip('?')


class WebServiceInterface(Interface):

    NotFound = NotFound
    MethodNotAllowed = MethodNotAllowed

    def __init__(self, *args, **kwargs):
        super(WebServiceInterface, self).__init__(*args, **kwargs)
        self.application = Request.application(self.dispatch_request)
        if self.container.debug:
            from werkzeug.debug import DebuggedApplication
            self.application = DebuggedApplication(self.application, evalex=True)
        self.wsgi_server = None
        self.uses_static_port = True
        self.http_socket = None

    def __call__(self, *args, **kwargs):
        # Make the object itself a WSGI app
        return self.application(*args, **kwargs)

    def apply_config(self, config):
        super(WebServiceInterface, self).apply_config(config)
        self.http_port = config.get('port')
        self.pool_size = config.get('wsgi_pool_size')
        if not self.http_port:
            self.uses_static_port = False
            self.http_port = sockets.get_unused_port()

    def get_description(self):
        description = super(WebServiceInterface, self).get_description()
        description['http_port'] = self.http_port
        return description

    def on_start(self):
        super(WebServiceInterface, self).on_start()
        setup_logger('werkzeug')
        setup_logger('gevent')
        if self.uses_static_port:
            try:
                socket_fd = self.container.get_shared_socket_fd(self.http_port)
            except NoSharedSockets:
                pass
            except SocketNotCreated:
                logger.warning("socket for port %s wasn't created by node, binding from instance instead", self.http_port)
            else:
                self.http_socket = sockets.create_socket('fd://%s' % socket_fd)
        if not self.http_socket:
            address = '%s:%s' % (self.container.server.ip, self.http_port)
            self.http_socket = sockets.create_socket(address)
        self.wsgi_server = LymphWSGIServer(self.http_socket, self.application, spawn=Group(self.pool_size))
        self.wsgi_server.start()

    def on_stop(self, **kwargs):
        self.wsgi_server.stop()
        super(WebServiceInterface, self).on_stop()

    def dispatch_request(self, request):
        trace.set_id()
        logger.info('%s %s', request.method, request.path)
        urls = self.url_map.bind_to_environ(request.environ)
        request.urls = urls
        try:
            rule, kwargs = request.urls.match(method=request.method, return_rule=True)
        except NotFound:
            response = self.NotFound().get_response(request.environ)
        except MethodNotAllowed:
            response = self.MethodNotAllowed().get_response(request.environ)
        except HTTPException as ex:
            response = ex.get_response(request.environ)
        else:
            response = self.handle(request, rule, kwargs)
        response.headers['X-Trace-Id'] = trace.get_id()
        return response

    def handle(self, request, rule, kwargs):
        try:
            self.container.http_request_hook(request, rule, kwargs)
            handler = self.get_handler(request, rule)
            if hasattr(handler, "dispatch"):
                response = handler.dispatch(kwargs)
            else:
                response = handler(request, **kwargs)
        except MethodNotAllowed:
            response = self.MethodNotAllowed().get_response(request.environ)
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

    def get_handler(self, request, rule):
        if callable(rule.endpoint):
            handler = rule.endpoint(self, request)
        elif isinstance(rule, HandledRule):
            handler = rule.handler(self, request)
        else:
            handler = getattr(self, rule.endpoint)
        return handler

    def get_wsgi_application(self):
        return self.application
