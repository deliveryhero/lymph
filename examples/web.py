import lymph
import json

from lymph.web.interfaces import WebServiceInterface

from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Response


class JsonrpcGateway(WebServiceInterface):
    service_type = 'jsonrpc-gateway'
    http_port = 4080

    url_map = Map([
        Rule('/', endpoint='index'),
        Rule('/static/<path:path>', endpoint='static_resource'),
        Rule('/api/jsonrpc/<string:service_type>/', endpoint='jsonrpc'),
    ])

    def index(self, request):
        return self.static_resource(request, path='jsonrpc.html', content_type='text/html')

    def static_resource(self, request, path=None, content_type=None):
        with open('examples/static/%s' % path) as f:
            return Response(f.read(), content_type=content_type)

    def jsonrpc(self, request, service_type):
        req = json.load(request.stream)
        args = req['params'][0]
        result = self.request(service_type, str(req['method']), args)
        return Response(json.dumps({'result': {'result': result.body, 'gateway': self.container.endpoint}, 'error': None, 'id': req['id']}), content_type='application/json')
