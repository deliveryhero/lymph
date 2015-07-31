
.. _cli-lymph-instance:

.. program:: lymph instance

``lymph instance``
=================

Starts a service instance, e.g.:

.. code::

    $ lymph instance --config=some_service.yml

Options
-------

.. cmdoption:: --ip <address>

.. cmdoption:: --port <port>, -p <port>

    The instance will use this port for the RPC endpoint.

.. cmdoption:: --guess-external-ip, -g

    The instance will guess the public facing IP of the machine it runs on and
    uses it instead of --ip.

.. cmdoption:: -i, --isolated

    Isolated instances don't register with the service registry.

.. cmdoption:: --reload

    Automatically stops the service when imported Python files in the current
    working directory change. The process will be restarted by the node.
    Do not use this in production.
