Getting Started
================

Install lymph
~~~~~~~~~~~~~

.. code:: bash

    $ python setup.py install


Write an echo service
~~~~~~~~~~~~~~~~~~~~~~

Create a module called ``echo`` in your Python path.

.. code:: python

    import lymph


    class Echo(lymph.Interface):
        @lymph.rpc()
        def echo(self, channel, text=None):
            channel.reply(text)


Create a config file for this service (``echo.yml``)::

.. code:: yaml

    interfaces:
        echo:
            class: echo:Echo


Run the service
~~~~~~~~~~~~~~~

.. code:: bash

    $ lymph instance --config=echo.yml
    
