
Welcome to lymph's documentation!
=================================

lymph is a framework for Python services. lymph intends to be the glue between
your services so you don't get sticky fingers.

This is what a service looks like with lymph:

.. code:: python

    import lymph


    class Greeting(lymph.interface):

        @lymph.rpc()
        def greet(self, name):
            '''
            Returns a greeting for the given name
            '''
            print(u'Saying to hi to %s' % name)
            self.emit(u'greeted', {'name': name})
            return u'Hi, %s' % name

Contents:

.. toctree::
   :maxdepth: 2

   installation
   user_guide
   cli
   topic_guides/index
   api/index
   protocol
   glossary
   faq
   contributing


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

