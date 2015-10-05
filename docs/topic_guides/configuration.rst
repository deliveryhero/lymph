.. _config:

Configuration
=============

Lymph needs to be configured so that it knows how and where to find its service
registry and its event system.

.. code-block:: yaml

    container:
        registry:
            class: lymph.discovery.zookeeper:ZookeeperServiceRegistry
            zkclient:
                class: kazoo.client:KazooClient
                hosts: 120.0.0.1:2181
    
        events:
            class: lymph.events.kombu:KombuEventSystem
            transport: amqp
            hostname: 127.0.0.1

You can find this sample configuration file in :file:`conf/sample-node.yml`.


Environment Variables
~~~~~~~~~~~~~~~~~~~~~~

Lymph config files support environment variable substitution for string values:

.. code-block:: yaml

    key: protocol://$(env.USER):$(env.PASSWORD)@host/path


You can also inject structured environment configuration from a YAML file,
e.g. ``lymph -c conf.yml --vars=vars.yml command``:

.. code-block:: yaml

    # vars.yml
    key: value
    struct:
        foo: bar

.. code-block:: yaml

    # conf.yml
    foo: $(var.key)
    var: $(var.struct)
    interpolation: prefix_$(var.key)_suffix


Dependencies
------------

Lymph supports a way to inject dependencies from configuration file.

You start by defining a top level "dependencies" key that you want to inject
and share between different components, this should be in the format

.. code-block:: yaml

     dependencies:
         <name>:
             class: <class path>
             <extra class arguments>

Then you can reference a dependency anywhere in your configuration by
using the ``dep:<name>`` format, as shown in the example above.


Container Configuration
-----------------------

.. describe:: container.ip

    use this IP address. The :option:`--ip <lymph --ip>` option for 
    :program:`lymph` takes precedence. Default: ``127.0.0.1``.


.. describe:: container.port

    Use this port for the service endpoint. The :option:`--port <lymph --port>` 
    option for :program:`lymph` takes precedence. If no port is configured, lymph
    will pick a random port.


.. describe:: container.class

    the container implementation. You probably don't have to change this.
    Default: ``lymph.core.container:Container``

.. _config-container-log_endpoint:

.. describe:: container.log_endpoint

    the local ZeroMQ endpoint that should be used to publish logs via 
    the :ref:`_zmqpub <config-logging-_zmqpub>` handler.

.. describe:: container.pool_size

    Size of the pool of Greenlets, default is unlimited.


.. _registry-config:

Registry Configuration
----------------------

.. describe:: container.registry.class

Defaults to ``lymph.discovery.zookeeper:ZookeeperServiceRegistry``


ZooKeeper
~~~~~~~~~

To use `ZooKeeper`_ for serivce discovery set ``class`` to ``lymph.discovery.zookeeper:ZookeeperServiceRegistry``.


.. describe:: container.registry.zkclient

A reference to zookeeper client either as a dependency or a class.

.. _ZooKeeper: http://zookeeper.apache.org/


.. _event-config:

Event Configuration
-------------------

.. describe:: container.events.class


Kombu
~~~~~

To use the `kombu`_ backend set ``class`` to ``lymph.events.kombu:KombuEventSystem``.
All other keys will be passed as keyword arguments to the kombu `Connection <http://kombu.readthedocs.org/en/latest/userguide/connections.html#keyword-arguments>`_.


.. _kombu: kombu.readthedocs.org/


Null
~~~~

The null backend doesn't transport any events. Set ``class`` to ``lymph.events.null.NullEventSystem`` if that is what you want.


.. _interface-config:


Metrics Configuration
---------------------

.. describe:: container.metrics.tags

A dictionary of tags to be sent with all monitoring data from this container, e.g.

.. code:: yaml

    container:
        metrics:
            tags:
                env: $(env.NAMESPACE)


Interface Configuration
-----------------------

.. describe:: interfaces.<name>

    Mapping the name to instance which will be used to send requests
    and discover this interface.
    This name is also configuration that will be passed to the implementation's
    :meth:`lymph.Interface.apply_config()` method.

.. describe:: interfaces.<name>.class

    The class that implements this interface, e.g. a subclass of :class:`lymph.Interface`.


Components Configuration
------------------------

Extra component can be defined under the components namespace e.g ``SerialEventHandler``.


.. code-block:: yaml

    components:
        SerialEventHandler:
            zkclient: dep:kazoo



Logging Configuration
---------------------

.. describe:: logging

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


Debugging Configuration
-----------------------

.. describe:: debug.backdoor_ip

Specify which ip address the backdoor terminal should listen too.
