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
