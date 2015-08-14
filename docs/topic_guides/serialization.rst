Serialization
=============

Overview
~~~~~~~~

Lymph uses `msgpack`_ to serialize events and rpc arguments.
In addition to the types supported directly by msgpack, the lymph serializer 
also handles the following basic Python types:
``set``, ``datetime.datetime``, ``datetime.date``, ``datetime.time``, ``uuid.UUID``, and ``decimal.Decimal``.


.. _msgpack: www.msgpack.org


Object level serialization
~~~~~~~~~~~~~~~~~~~~~~~~~~

Object level serialization can be defined by implementing ``_lymph_dump_`` method in classes subject to serialization.

Object-level serialization can help to produce more concise code in certain situations, e.g.:

.. code:: python

    class Process(object):
        ...

        def _lymph_dump_(self):
            return {
                'pid': self.pid,
                'name': self.name,
            }


    class Node(lymph.Interface):

        @lymph.rpc()
        def get_processes(self, service_type=None):
            procs = []
            for proc in self._processes:
                if not service_type or proc.service_type == service_type:
                    procs.append(proc)
            return procs

        @lymph.rpc()
        def stop(self, service_type=None):
            for proc in self.get_processes(service_type):
                proc.stop()

In the example above by defining the ``_lymph_dump_`` in our Process class, we were able to reuse the rpc
function ``get_processes``.
