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
