Command Line Interface
======================

Many iris commands produce unicode output. Therefore, you'll have to set your
locale (LC_ALL or LC_CTYPE) to UTF-8.

If you want to pipe iris commands with python2, you might have to set 
PYTHONIOENCODING to UTF-8 as well.

.. program:: iris

The following options apply to all subcommands:

.. cmdoption:: --ip <address>

.. cmdoption:: -p <port>, --port <port>

.. cmdoption:: -g, --guess-external-ip

.. cmdoption:: -c <file>, --config <file>

    Read the configuration from <file>. This can also be specified as an environment
    variable :envvar:`IRIS_CONFIG`. The default value is ``.iris.yml``.

.. cmdoption:: --loglevel <level>

.. cmdoption:: --logfile <file>


.. _cli-iris-discover:

.. program:: iris discover

``iris discover``
~~~~~~~~~~~~~~~~~


.. _cli-iris-inspect:

.. program:: iris inspect

``iris inspect``
~~~~~~~~~~~~~~~~



.. _cli-iris-instance:

.. program:: iris instance

``iris instance``
~~~~~~~~~~~~~~~~~

.. cmdoption:: -i, --isolated

    Isolated instances don't register with the service registry.


.. _cli-iris-node:

.. program:: iris node

``iris node``
~~~~~~~~~~~~~


.. _cli-iris-request:

.. program:: iris request

``iris request``
~~~~~~~~~~~~~~~~


