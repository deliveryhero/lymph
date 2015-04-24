Serialization
=============

Overview
~~~~~~~~

Payloads that are transmitted via messages need to be serialised.
Lymph uses `msgpack`_ (a binary representation of JSON) for this by default, but a plain JSON serializer is also available.

In addition to the types supported directly by JSON, the lymph serializer also handles the following basic Python types:
``set``, ``datetime.datetime``, ``datetime.date``, ``datetime.time``, and ``decimal.Decimal``.


Implementation Details
~~~~~~~~~~~~~~~~~~~~~~

The custom serialisation types are added in a wrapping to the JSON, so that the original type
can be deserialized. The wrapping has the following form:

.. code:: json

	{
		"__type__": "<type-name>",
		"_": "… serialized data …"
	}



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
