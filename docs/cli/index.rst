
Command Line Interface
======================

Lymph's cli lets you run, discover, inspect and interact with services. It is
built to be your toolbelt when developing and running services. The cli is
extensible. You can write custom lymph subcommands, e.g. `lymph top`_.

.. note::

    Many of lymph's commands produce unicode output. Therefore, you'll have to
    set your locale (LC_ALL or LC_CTYPE) to UTF-8.

    If you want to pipe lymph commands with Python 2, you might have to set
    PYTHONIOENCODING to UTF-8 as well.


.. toctree::
   :maxdepth: 1

   common_options
   list
   help
   instance
   discover
   inspect
   emit
   request
   subscribe
   node
   shell
   config


.. _lymph top: http://github.com/mouadino/lymph-top
