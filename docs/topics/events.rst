Events
======

Overview
~~~~~~~~

Lymph uses events to communicate between various services. For this, `RabbitMQ`_
is currently used to do the event passing. Services can emit events and
subscribe to the queue to consume events. 

The way events are communicated is pluggable and can be easily exchanged at will.
The unittests for instance are using a local event system ``LocalEventSystem`` to
not rely on `RabbitMQ`_.

Other event brokers
~~~~~~~~~~~~~~~~~~~

Lymph allows other event brokers to be easily incorporated. Lymph also 
provides the following additional event broker services:

- Null (a black hole)
- Local (simple event broker that runs in the scope of the main lymph process)
- Kombu (interfaces to `RabbitMQ`_ as a broker using the `kombu`_ library)

The event broker service can be set in the :file:`.lymph.yml` configuration file:

.. code:: yaml

    container:
        events:
            class: lymph.events.kombu:KombuEventSystem
            transport: amqp
            hostname: 127.0.0.1

See :ref:`event-config` for details.


Subscribing to events
~~~~~~~~~~~~~~~~~~~~~

In order to have methods executed whenever a given event is emitted, you decorate
the function with the ``event`` decorator.

.. decorator:: event(*event_types)

    :param event_types: may contain wildcards (``#`` matching zero or more words and 
                        ``*`` matches one word), e.g. ``'subject.*'``

    Marks the decorated interface method as an event handler.
    The service container will automatically subscribe to given ``event_types``.
    
    .. code::
    
        import lymph
        
        class Example(lymph.Interface):
            @lymph.event('task_done')
            def on_task_done(self, event):
                assert isinstance(event, lymph.core.events.Event)

A new queue will be created for every service name and event handler combination.


Dynamically subscribing to events
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Subscribing to events using the ``event`` decorator only works at service instantiation time.
If you need to subscribe to events at runtime, you need to use the ``subscribe`` decorator:

.. decorator:: subscribe(*event_types, sequential=True)

    Behaves like :func:`lymph.event`, but can be used at runtime
    
    .. code::
    
        class Example(lymph.Service):
            def on_start(self):
                @self.subscribe('dynamic_event_type')
                def on_event(event):
                    assert isinstance(event, lymph.core.events.Event)


Emitting events
~~~~~~~~~~~~~~~

The ``lymph.Interface`` provides a method for emitting events. 

.. method:: lymph.Interface.emit(self, event_type, payload)
    :noindex:

    :param event_type: name of the event
    :param payload: a dict of :ref:`serializable <serialization>` data structures


A simple example of a class emitting a signal with a simple event would be:

.. code:: 

	class SomeClass(lymph.Interface):
		def emit_event(self):
			self.emit('simple_event', {'article': 'foo', 'quantity': 5})


Command line interface
~~~~~~~~~~~~~~~~~~~~~~

To interact with the event system from the command line, the following
commands are available:

.. code:: bash

	$ lymph subscribe

and

.. code:: bash

	$ lymph emit

lymph subscribe
^^^^^^^^^^^^^^^

With this command, you can register to a specific event and have all events
printed out on stdout.

For the default example services, this might be:

.. code:: bash

	$ lymph subscribe uppercase_transform_finished
	uppercase_transform_finished: {'text': u'foo_282'}
	uppercase_transform_finished: {'text': u'foo_283'}
	uppercase_transform_finished: {'text': u'foo_284'}
	…

This lists all the events sent to ``uppercase_transform_finished`` produced by
the demo loop which calls the echo service. Each line represents an individual
event, stating its name and its payload.

You can also subscribe to multiple events at once:

.. code:: bash

	$ lymph subscribe event_a event_b
	event_a: {u'data': u'nice'}
	event_b: {u'information': u'data'}


lymph emit
^^^^^^^^^^

With this command, you can manually emit a specific event from the command line.
You need to specify the name of the event and provide a JSON encoded body.

For the default example services, this might be:

.. code:: bash

	$ lymph emit uppercase_transform_finished '{"text": "bar_foo_234"}'

This would emit an event with the name ``uppercase_transform_finished`` with the given
payload to any service that is listening to this event. We can inspect the events
sent through the system with the `lymph subscribe`_ command in another terminal:

.. code:: bash

	$ lymph subscribe uppercase_transform_finished
	…
	uppercase_transform_finished: {'text': u'foo_2629'}
	uppercase_transform_finished: {'text': u'foo_2630'}
	uppercase_transform_finished: {u'text': u'bar_foo_234'}
	uppercase_transform_finished: {'text': u'foo_2631'}
	…

We can see that the event has been routed to the instance along with all the
other events from the demo loop.

.. _rabbitmq: www.rabbitmq.com
.. _kombu: kombu.readthedocs.org/
