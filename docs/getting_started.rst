Getting Started
================

Install lymph
~~~~~~~~~~~~~

Installing lymph can be as easy as:

.. code:: bash

    $ pip install lymph

If you want use Python 3, you have to install the latest gevent version from github first:

.. code:: bash

    $ pip install git+https://github.com/surfly/gevent.git#egg=gevent


Please refer to the :doc:`installation guide <installation>` for more detailed instructions.


Write an echo service
~~~~~~~~~~~~~~~~~~~~~~

Create a module called ``echo`` in your Python path.

.. code:: python

    import lymph


    class Echo(lymph.Interface):
        @lymph.rpc()
        def echo(self, text=None):
            return text


Create a config file for this service (``echo.yml``):

.. code:: yaml

    interfaces:
        echo:
            class: echo:Echo


Run the service
~~~~~~~~~~~~~~~

.. code:: bash

    $ lymph instance --config=echo.yml
    
