Running services
================

Overview
~~~~~~~~

There are two ways to start services with lymph. You can either start a lymph
service directly from the command line using ``lymph instance`` or define
all the services to start in a configuration file and start them all with
lymph's development server ``lymph node``.


lymph instance
~~~~~~~~~~~~~~

This command runs a single service instance given a config file with :ref:`interfaces <interface-config>`

.. code:: bash

    lymph instance --config=$PATH_TO_CONFIG_FILE



Writing configuration files for ``lymph instance``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A configuration file of a lymph service requires the following sections:

    - container
    - interfaces

You need to define a separate configuration file for each service or instance setup. If you have many services
running, which would be the normal case in a productive lymph setup, the same information about ``container`` 
would be present in each file. In order to avoid having to copy the same information into every
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

.. describe:: interfaces.<name>

    Mapping from service name to instance configuration that will be passed to
    the implementation's :meth:`lymph.Service.apply_config()` method.

which gives a name to a specific interface (i.e. the ``namespace`` part when referencing a service). If the interface
has been named, it needs to be linked to a class that is a subclass of :class: `lymph.Interface`.

.. describe:: interfaces.<name>.class

    The class that implements this interface, e.g. a subclass of :class:`lymph.Interface`.

After the interface class has been defined, any additional configuration can be passed on to the interface class by
defining any

.. describe:: interfaces.<name>.<param>

    The whole ``interfaces.<name>`` dict is available as configuration for the
    interface class.


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
-----------

This command will start instances of services as defined in a configuration file.
It will load as many instances as specified for each defined service. By default it will
read the ``.lymph.yml`` file, but through the ``--config`` option, you can specify another
configuration. You run this command by initiating:

.. code:: bash

    $ lymph node


Configuring ``lymph node``
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. describe:: instances.<name>

Besides the usual configuration sections for the ``container``, a
section on ``instances`` needs to be added. In this section, each service is defined,
together with the ``lymph instance`` command to start it, and the number of processes 
``numprocesses`` each service should have.

.. describe:: instances.<name>.command:

    A command (does not necessarily have to be a ``lymph instance`` command) that will
    be spawned by ``lymph node``

.. describe:: instances.<name>.numprocesses:

    Number of times the defined command is spawned


An example of such an ``instances`` configuration block:

.. code::

    instances:
        echo:
            command: lymph instance --config=conf/echo.yml
            numprocesses: 10

        demo:
            command: lymph instance --config=conf/demo.yml

