.. _getting-started:


Getting Started
================

Install lymph
~~~~~~~~~~~~~

Installing lymph can be as easy as:

.. code:: bash

    $ pip install lymph

Please refer to the :doc:`installation guide <installation>` for more detailed instructions.

.. note::

    You'll also need `ZooKeeper`_ and `RabbitMQ`_ on localhost to run the following examples.


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

    container:
        registry:
            class: lymph.discovery.zookeeper:ZookeeperServiceRegistry
            zkclient:
                class: kazoo.client:KazooClient

        events:
            class: lymph.events.kombu:KombuEventSystem

    interfaces:
        echo:
            class: echo:Echo


Run the service
~~~~~~~~~~~~~~~

.. code:: bash

    $ lymph instance --config=echo.yml


Next Steps
~~~~~~~~~~

You can find a more complete introduction to lymph in Max Brauer's `import lymph`_ presentation.


.. _ZooKeeper: http://zookeeper.apache.org
.. _RabbitMQ: http://www.rabbitmq.com/
.. _import lymph: http://import-lymph.link
