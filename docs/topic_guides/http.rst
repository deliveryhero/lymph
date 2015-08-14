HTTP
====

.. code-block:: python

    from lymph.web.interfaces import WebServiceInterface
    from werkzeug.routing import Map, Rule
    from werkzeug.wrappers import Response


    class HttpHello(WebServiceInterface)
        url_map = Map([
            Rule('/hello/<string:name>/', endpoint='hello'),
        ])
        
        def hello(self, request, name):
            return Response('hello %s!' % name)
