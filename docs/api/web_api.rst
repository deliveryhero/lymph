.. currentmodule:: lymph.web


Web API
========

.. class:: WebServiceInterface

    .. attribute:: application
    
        WSGI application instance that this interface is running
        
    .. attribute:: url_map
    
        A `werkzeug.routing.Map`_ instance that is used to map requests to
        request handlers. Typically given as a class attribute.


.. _werkzeug.routing.Map: http://werkzeug.pocoo.org/docs/0.10/routing/#maps-rules-and-adapters