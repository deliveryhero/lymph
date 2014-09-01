
FAQ
===

.. contents::
    :local:

Why does lymph crash with UnicodeDecodeError: 'ascii' codec can't encode character …?
--------------------------------------------------------------------------------------

Since many lymph commands produce unicode output, you have to set your locale to UTF-8, e.g. with

.. code:: bash

    $ export LC_ALL=en_US.UTF-8

If you want to pipe lymph commands with Python 2, you might also have to set ``PYTHONIOENCODING``

.. code:: bash

    $ export PYTHONIOENCODING=UTF-8
