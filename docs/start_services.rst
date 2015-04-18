Starting services
=================

Overview
~~~~~~~~

There are two ways to start services with lymph. You can either start a lymph
service directly from the command line using ``lymph instance`` or define
all the services to start in a configuration file and start them all with
``lymph node``.

lymph instance
~~~~~~~~~~~~~~

With this command you can start a single service as one process as follows:

.. code:: bash

    lymph instance [--ip=<address> | --guess-external-ip | -g]
                         [--port <port> | -p <port>] [--reload] [--debug]
                         [--interface=<cls>]... [options]

where

.. code:: bash

    Options:
      --ip=<address>               Use this IP for the service.
      --port=<port>                Use this port for the service.
      --guess-external-ip, -g      Guess the public facing IP of this machine and
                                   use it instead of the provided address.
      --reload                     Reloads the service if the sources of the service
                                   changed
      --debug                      Opens this service within a gevent backdoor service on
                                   127.0.0.1:5005
      --interface=<cls>            load the <cls> as a service
      --isolated                   isolated instances don't register with the service registry

    Important default options:
      --config=<config_file>       Load service using this config file
    
In order to start a lymph service, you need to specify a configuration file to use with
``--config`` (if none is provided, the ``.lymph.yml`` file will be used). ``lymph instance``
needs to read the ``container`` and ``event_system`` part of the configuration file to properly
setup and start the service. The setup of the individual instance is then handled through the
``interface`` section which is explained below.

If you want to keep your service configuration files free from the ``container`` and the
``event_system`` part, you can specify a default config file to be read, using the 
``LYMPH_NODE_CONFIG`` environmental variable. You might want to set

.. code:: bash

    $ export LYMPH_NODE_CONFIG="/path/to/lymph/config/.lymph.yml"

With the ``interface`` option, you can directly specify a class that inherits from ``lymph.Instance``
and run that class inside a container:

.. code:: bash

    $ lymph instance --config=conf/echo.yml --interface=examples:EchoService

In this example, a new instance of the example EchoService is started by specifying the
class directly as ``examples:EchoService``.


Writing configuration files for ``lymph instance``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A configuration file of a lymph service requires the following sections:

    - container
    - event_system
    - interfaces

You need to define a separate configuration file for each service or instance setup. If you have many services
running, which would be the normal case in a productive lymph setup, the same information about ``container`` and
``event_system`` would be present in each file. In order to avoid having to copy the same information into every
file and obtain a configuration mess, it is possible to set a default configuration file where lymph extracts the
necessary information. This is usually the ``.lymph.yml`` file, which is also needed by ``lymph node`` (the standard
way to start lymph services, see :doc: ``lymph node`` below).

The default configuration file is set using the ``LYMPH_NODE_CONFIG`` environmental variable and is usually set by

.. code:: bash

    $ export LYMPH_NODE_CONFIG="/path/to/lymph/config/.lymph.yml"

.. describe:: interfaces

Each service needs to have its ``interfaces`` defined in the respective service configuration file. The ``interfaces``
section defines which endpoints a service has (a service can have multiple endpoints) and the configuration of
each endpoint (you can have multiple endpoints to the same service interface class, with different configurations).

The interfaces section is made up of

.. describe:: interfaces:<name>

    Mapping from service name to instance configuration that will be passed to
    the implementation's :meth:`lymph.Service.apply_config()` method.

which gives a name to a specific interface (i.e. the ``namespace`` part when referencing a service). If the interface
has been named, it needs to be linked to a class that is a subclass of :class: `lymph.Interface`.

.. describe:: interfaces:<name>:class:

    The class that implements this interface, e.g. a subclass of :class:`lymph.Interface`.

After the interface class has been defined, any additional configuration can be passed on to the interface class by
defining any

.. describe:: interfaces:<name>:<option_name>:

    Option to be passed on to the interface class.

A simple example for an interface definition is:

.. code:: yaml

    interfaces:
        echo:
            class: echo:EchoService

and another example showing the use of additional interface options and the definition of multiple interfaces:

.. code:: yaml

    interfaces:
        echo_small_valley:
            class: echo:EchoService
            delay: 1

        echo_large_valley:
            class: echo:EchoService
            delay: 10

lymph node
~~~~~~~~~~

This command will start instances of services as defined in a configuration file.
It will load as many instances as specified for each defined service. By default it will
read the ``.lymph.yml`` file, but through the ``--config`` option, you can specify another
configuration. You run this command by initiating:

.. code:: bash

    $ lymph node

Configuring ``lymph node``
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. describe:: instances:<name>

Besides the usual configuration sections for the ``container`` and the ``event_system``, a
section on ``instances`` needs to be added. In this section, each service is defined,
together with the ``lymph instance`` command to start it, and the number of processes 
``numprocesses`` each service should have.

.. describe:: instances:<name>:command:

    A command (does not necessarily have to be a ``lymph instance`` command) that will
    be spawned by ``lymph node``

.. describe:: instances:<name>:numprocesses:

    Number of times the defined command is spawned

You will need for each service instance another configuration file, as described above
for ``lymph instance`` where all the parameters of the service itself are specified.

An example of such an ``instances`` configuration block:

.. code::

    instances:
        echo:
            command: lymph instance --config=conf/echo.yml
            numprocesses: 10

        conf_entry_can_have_different_name_than_service:
            command: lymph instance --config=conf/demo.yml

The service type (i.e. in the example above the ``echo`` and ``conf_entry_can_have_different_name_than_service``
entries) can have different names as the actual services themselves. However it is advised for orders
sake to keep them equal.
