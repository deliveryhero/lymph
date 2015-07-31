
.. _cli-lymph-node:

.. program:: lymph node

``lymph node``
==============

This is lymph's development server. It runs any number of services and
instances for you. It is being configured via ``.lymph.yml`` by default or any other
configuration file you point it to.

The lymph configuration can be extended like this to bring up two ``echo`` instances,
one ``demo`` instance and your redis server:

.. code:: yaml

    # ...

    instances:
        echo:
            command: lymph instance --config=conf/echo.yml
            numinstances: 2

        demo:
            command: lymph instance --config=conf/demo.yml

        redis:
            command: ./redis-server

This command takes the same commandline options as ``lymph instance``.

Options
-------

.. FIXME
