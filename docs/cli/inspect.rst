
.. _cli-lymph-inspect:

.. program:: lymph inspect

``lymph inspect``
=================

Lists the RPC methods of the given interface, including their docstrings:

.. code:: console

    $ lymph inspect echo

    rpc echo.upper(text)
        

    rpc echo.echo(text)
        Simple service relaying whatever comes in

    rpc lymph.status()
        

    rpc lymph.inspect()
        Returns a description of all available rpc methods of this service

    rpc lymph.ping(payload)

Options
-------

.. FIXME
