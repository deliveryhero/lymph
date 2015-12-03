Versioning interfaces
======================


.. code:: yaml

    interfaces:
        echo@1.5.0:
            class: echo:Echo
        
        echo@2.0.0:
            class: echo:Echo2
            
        


Requesting Specific Versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from the command line:

.. code:: console

    $ lymph request echo.upper@1.2 '{"text": "foo"}'


from code:

.. code:: python

    proxy = lymph.proxy('echo', version='1.1')

