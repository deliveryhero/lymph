Getting Started
================

Install iris
~~~~~~~~~~~~

.. code:: bash

    $ python setup.py install


Write an echo service
~~~~~~~~~~~~~~~~~~~~~~

Create a module called ``echo`` in your Python path.

.. code:: python

    import iris


    class Echo(iris.Interface):
        service_type = 'echo'

        @iris.rpc()
        def echo(self, channel, text=None):
            channel.reply(text)


Run the service
~~~~~~~~~~~~~~~

.. code:: bash

    $ iris instance echo:Echo
    
