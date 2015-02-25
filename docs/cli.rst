Command Line Interface
======================

Many lymph commands produce unicode output. Therefore, you'll have to set your
locale (LC_ALL or LC_CTYPE) to UTF-8.

If you want to pipe lymph commands with Python 2, you might have to set
PYTHONIOENCODING to UTF-8 as well.

.. program:: lymph

The following options apply to all subcommands:

.. cmdoption:: --config <file>, -c <file>

    Read the configuration from <file>. This can also be specified as an environment
    variable :envvar:`LYMPH_CONFIG`. The default value is ``.lymph.yml``.

.. cmdoption:: --loglevel <level>

.. cmdoption:: --logfile <file>

.. cmdoption:: --color

    Force output coloring

.. cmdoption:: --no-color

    Disable output coloring


.. _cli-lymph-discover:

.. program:: lymph discover

``lymph discover``
~~~~~~~~~~~~~~~~~~


.. _cli-lymph-inspect:

.. program:: lymph inspect

``lymph inspect``
~~~~~~~~~~~~~~~~~



.. _cli-lymph-instance:

.. program:: lymph instance

``lymph instance``
~~~~~~~~~~~~~~~~~~

.. cmdoption:: --ip <address>

.. cmdoption:: --port <port>, -p <port>

.. cmdoption:: --guess-external-ip, -g

.. cmdoption:: -i, --isolated

    Isolated instances don't register with the service registry.

.. cmdoption:: --reload

    Automatically stops the service when imported Python files in the current
    working directory change. The process will be restarted by the node.
    Do not use this in production.


.. _cli-lymph-node:

.. program:: lymph node

``lymph node``
~~~~~~~~~~~~~~

This command takes the same commandline options as ``lymph instance``.


.. _cli-lymph-request:

.. program:: lymph request

``lymph request``
~~~~~~~~~~~~~~~~~


.. _cli-lymph-shell:

``lymph shell``
~~~~~~~~~~~~~~~

Starts an interactive Python shell, locally or remotely.

Locally:
--------

In case shell was open locally the following objects will be available in the
global namespace:

``client``
    a configured :class:`lymph.client.Client` instance

``config``
    a loaded :class:`lymph.config.Configuration` instance

Remotely:
---------

``lymph shell --remote=<name>`` can open a remote shell in a running services, but only
if this service was run in ``--debug`` mode.

In this shell you can have access to the current container instance as to some helper
functions for debugging purposes:

``container``
    the :class:`lymph.core.container.Container`` instance

``dump_stacks()``
    helper function to dump stack of all running greenlets and os threads.
