
.. _cli-lymph-shell:

.. program:: lymph shell

``lymph shell``
===============

Starts an interactive Python shell, locally or remotely.

Locally
-------

In case shell was open locally the following objects will be available in the
global namespace:

``client``
    a configured :class:`lymph.client.Client` instance

``config``
    a loaded :class:`lymph.config.Configuration` instance

Remotely
--------

``lymph shell --remote=<name>`` can open a remote shell in a running services, but only
if this service was run in ``--debug`` mode.

In this shell you can have access to the current container instance as to some helper
functions for debugging purposes:

``container``
    the :class:`lymph.core.container.Container` instance

``dump_stacks()``
    helper function to dump stack of all running greenlets and os threads.

Options
-------

.. FIXME
