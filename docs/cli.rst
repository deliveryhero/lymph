Command Line Interface
======================

Many lymph commands produce unicode output. Therefore, you'll have to set your
locale (LC_ALL or LC_CTYPE) to UTF-8.

If you want to pipe lymph commands with python2, you might have to set 
PYTHONIOENCODING to UTF-8 as well.

.. program:: lymph

The following options apply to all subcommands:

.. cmdoption:: --ip <address>

.. cmdoption:: -p <port>, --port <port>

.. cmdoption:: -g, --guess-external-ip

.. cmdoption:: -c <file>, --config <file>

    Read the configuration from <file>. This can also be specified as an environment
    variable :envvar:`IRIS_CONFIG`. The default value is ``.lymph.yml``.

.. cmdoption:: --loglevel <level>

.. cmdoption:: --logfile <file>


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

.. cmdoption:: -i, --isolated

    Isolated instances don't register with the service registry.


.. _cli-lymph-node:

.. program:: lymph node

``lymph node``
~~~~~~~~~~~~~~


.. _cli-lymph-request:

.. program:: lymph request

``lymph request``
~~~~~~~~~~~~~~~~~


.. _cli-lymph-shell:

``lymph shell``
~~~~~~~~~~~~~~~

Starts an interactive Python shell. The following objects will be available in the global namespace:

``client``
    a configured :class:`lymph.client.Client` instance

