
.. _cli-lymph-discover:

.. program:: lymph discover

``lymph discover``
=================

Prints a list of running services (and optionally instances), e.g.:

.. code::

    $ lymph discover
    some_service [2]
    another_service [1]

Options
-------

.. cmdoption:: --instances

   Details for every single instance will be included.

.. cmdoption:: --json

    Formats the output as JSON.

.. cmdoption:: --ip=<address>
  
    Use this IP for all sockets.

.. FIXME what does that mean? ^

.. cmdoption:: --guess-external-ip, -g

    The instance will guess the public facing IP of the machine it runs on and
    uses it instead of --ip.

.. cmdoption:: --only-running
