
.. _cli-lymph-config:

.. program:: lymph config

``lymph config``
=================

Prints the configuration.

.. code:: console

    $ lymph config

    container:
      events: {class: 'lymph.events.kombu:KombuEventSystem', hostname: 127.0.0.1, transport: amqp}
      ip: 127.0.0.1
      log_endpoint: tcp://127.0.0.1:62081
      registry: {class: 'lymph.discovery.zookeeper:ZookeeperServiceRegistry', zkclient: 'dep:kazoo'}
    dependencies:
      kazoo: {class: 'kazoo.client:KazooClient', hosts: '127.0.0.1:2181'}
    instances:
      demo: {command: lymph instance --config=conf/demo.yml}
      echo: {command: lymph instance --config=conf/echo.yml}
