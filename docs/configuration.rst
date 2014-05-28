Service Configuration Files
===========================

.. code-block:: yaml

    registry:
        class: iris.discovery.zookeeper:ZookeeperServiceRegistry
        hosts: 127.0.0.1:2181
    
    event_system:
        class: iris.events.kombu:KombuEventSystem
        transport: amqp
        hostname: 127.0.0.1

You can find this sample configuration file in :file:`conf/service.yml`.


Container Configuration
-----------------------

.. describe:: container:ip:

    use this IP address. The :option:`--ip <iris --ip>` option for 
    :program:`iris` takes precedence. Default: ``127.0.0.1``.


.. describe:: container:port:

    Use this port for the service endpoint. The :option:`--port <iris --port>` 
    option for :program:`iris` takes precedence. If no port is configured, iris
    will pick a random port.


.. describe:: container:class:

    the container implementation. You probably don't have to change this.
    Default: ``iris.core.container:Container``

.. _config-container-log_endpoint:

.. describe:: container:log_endpoint:

    the local ZeroMQ endpoint that should be used to publish logs via 
    the :ref:`_zmqpub <config-logging-_zmqpub>` handler.


.. _interface-config:

Interface Configuration
-----------------------

.. describe:: interfaces:<name>

    Mapping from service name to instance configuration that will be passed to
    the implementation's :meth:`iris.Service.apply_config()` method.
    
.. describe:: interfaces:<name>:class:

    The class that implements this interface, e.g. a subclass of :class:`iris.Service`.

Registry Configuration
----------------------

.. describe:: registry:class:

Defaults to ``iris.discovery.zookeeper:ZookeeperServiceRegistry``


ZooKeeper
~~~~~~~~~

To use `ZooKeeper`_ for serivce discovery set ``class`` to ``iris.discovery.zookeeper:ZookeeperServiceRegistry``.


.. describe:: registry:hosts: 127.0.0.1:2181

    A comma separated sequence of ZooKeeper hosts.


.. describe:: registry:chroot: /iris

    A path that will be used as a prefix for all znodes managed by iris.


.. _ZooKeeper: http://zookeeper.apache.org/


Simple
~~~~~~

To use the builtin serivce discovery mechanism set ``class`` to ``iris.discovery.service:IrisCoordinatorServiceRegistry``.

.. describe:: registry:coordinator_endpoint:

    Endpoint of the coordinator service (``iris.services.coordinator:Coordinator``).
    The environment variable :envvar:`IRIS_COORDINATOR` takes precedence.


Event Configuration
-------------------

.. describe:: event_system:class: iris.events.kombu:KombuEventSystem


Kombu
~~~~~

To use the `kombu`_ backend set ``class`` to ``iris.events.kombu:KombuEventSystem``.
All other keys will be passed as keyword arguments to the kombu `Connection <http://kombu.readthedocs.org/en/latest/userguide/connections.html#keyword-arguments>`_.


.. _kombu: kombu.readthedocs.org/

Simple
~~~~~~

To use the builtin broker service for event transport set ``class`` to ``iris.events.simple:SimpleEventSystem``.

Null
~~~~

The null backend doesn't transport any events. Set ``class`` to ``iris.events.null.NullEventSystem`` if that is what you want.


Logging Configuration
---------------------

.. describe:: logging:

Logging can be configured in standard `dictConfig`_ format. 
In addition to the setup provided via ``logging``, one formatter and two 
handlers are created. You can change them by providing different configuration
for the ids.

The formatter (``_trace``) includes the trace-id and is used for both built-in
handlers.

.. _config-logging-_zmqpub:

The ``_zmqpub`` handler publishes log messages on a ZeroMQ pub socket (see 
:ref:`container.log_endpoint <config-container-log_endpoint>`). 

The ``_console`` handler writes messages to either stdout or the file given by 
:option:`--logfile`. The level of the handler is set to 
:option:`--loglevel`.


.. _dictConfig: https://docs.python.org/2/library/logging.config.html#configuration-dictionary-schema
