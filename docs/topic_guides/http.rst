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


.. class:: WebServiceInterface

    .. method:: is_healthy()


Interface configuration
~~~~~~~~~~~~~~~~~~~~~~~~

.. describe:: interfaces.<name>.healthcheck.enabled

     Boolean: whether to respond to requests to ``interfaces.<name>.healthcheck.endpoint``.
     Defaults to ``True``.
     
.. describe:: interfaces.<name>.healthcheck.endpoint

    Respond with 200 to requests for this path as long as :meth:`is_healthy() <lymph.web.interfaces.WebServiceInterface.is_healthy>` returns True, and 503 otherwise.
    Defaults to ``"/_health/"``.

.. describe:: interfaces.<name>.port

    Listen on this port. Defaults to a random port.

.. describe:: interfaces.<name>.wsgi_pool_size

.. describe:: interfaces.<name>.tracing.request_header

    Name of an HTTP request header that may provide the trace id.
    Defaults to ``None``.

.. describe:: interfaces.<name>.tracing.response_header

    Name of the HTTP response header that contains the trace id.
    Defaults to ``"X-Trace-Id"``.
