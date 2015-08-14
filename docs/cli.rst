:tocdepth: 1

Command Line Interface
======================

Lymph's cli lets you run, discover, inspect and interact with services. It is
built to be your toolbelt when developing and running services. The cli is
extensible. You can write custom lymph subcommands, e.g. `lymph top`_.

.. contents::
    :local:

.. note::

    Many of lymph's commands produce unicode output. Therefore, you'll have to
    set your locale (LC_ALL or LC_CTYPE) to UTF-8.

    If you want to pipe lymph commands with Python 2, you might have to set
    PYTHONIOENCODING to UTF-8 as well.

    Check the :ref:`FAQ <faq>`.


This is an overview of lymph's cli. We don't document every command's
arguments and parameters on purpose. Each is self-documenting:

.. code:: bash

    $ lymph help <command>  # or
    $ lymph <command> --help


lymph list
------------

Prints a list of all available commands with their description.


lymph instance
----------------

Runs a service instance.


lymph discover
----------------

Discovers all available services and their instances, e.g.:


lymph inspect
---------------

Prints the RPC interface of a service with signature and docstrings.


lymph request
---------------

Invokes an RPC method of a service and prints the response.


lymph emit
------------

Emits an event in the event system.


lymph subscribe
-----------------

Subscribes to an event type and prints every occurence.


lymph node
------------

This is lymph's development server. It can run any number of services with any
number of instances as well as any other dependency.


lymph shell
-------------

Starts an interactive Python shell for service instance, locally or remotely.


lymph config
--------------

Prints configuration for inspection



.. _lymph top: http://github.com/mouadino/lymph-top
