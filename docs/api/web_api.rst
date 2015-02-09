.. currentmodule:: lymph.web


Web API
========

.. class:: WebServiceInterface

    .. attribute:: default_http_port = 4080

        If there's no port provided in the interface config, the http interface
        is bound to this port.
    
    .. attribute:: application
    
        WSGI application instance that this interface is running
        
    .. attribute:: url_map
    
        A `werkzeug.routing.Map`_ instance that is used to map requests to
        request handlers.


.. _werkzeug.routing.Map: http://werkzeug.pocoo.org/docs/0.10/routing/#maps-rules-and-adapters