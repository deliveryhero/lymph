Getting Started
================

Install lymph
~~~~~~~~~~~~µ

.. code:: bash

    $ python setup.py install


Write an echo service
~~~~~~~~~~~~~~~~~~~~~~

Create a module called ``echo`` in your Python path.

.. code:: python

    import lymph


    class Echo(lymph.Interface):
        service_type = 'echo'

        @lymph.rpc()
        def echo(self, channel, text=None):
            channel.reply(text)


Run the service
~~~~~~~~~~~~~~~

.. code:: bash

    $ lymph instance echo:Echo
    
