.. currentmodule:: lymph.core.container


Core API
========


.. class:: ServiceContainer

    .. classmethod:: from_config(config, **kwargs)

    .. method:: start()

    .. method:: stop()

    .. method:: send_message(address, msg)

        :param address: the address for this message; either a ZeroMQ endpoint or an lymph:// url
        :param msg: the :class:`lymph.core.messages.Message` object that will be sent
        :return: :class:`lymph.core.channels.ReplyChannel`

    .. method:: lookup(address)

        :param address: an lymph address
        :return: :class:`lymph.core.services.Service` or :class:`lymph.core.services.ServiceInstance`


.. currentmodule:: lymph.core.channels

.. class:: RequestChannel()

    .. method:: reply(body)

        :param body: a JSON serializable data structure

    .. method:: ack()

        acknowledges the request message


.. class:: ReplyChannel()

    .. method:: get(timeout=1)

        :return: :class:`lymph.core.messages.Message`

        returns the next reply message from this channel. Blocks until the reply
        is available. Raises :class:`Timeout <lymph.exceptions.Timeout>` after ``timeout`` seconds.


.. currentmodule:: lymph.core.messages

.. class:: Message

    .. attribute:: id

    .. attribute:: type

    .. attribute:: subject

    .. attribute:: body

    .. attribute:: packed_body


.. currentmodule:: lymph.core.services


.. class:: Service()

    Normally created by :meth:`ServiceContainer.lookup() <lymph.core.container.ServiceContainer.lookup()>`.
    Service objects represent lymph services.

    .. method:: connect()

        :return: :class:`lymph.core.connection.Connection` to an instance of this service.

    .. method:: disconnect()

        Disconnects all connections to instances of this service.

    .. method:: __iter__()

        Yields all known :class:`instances <ServiceInstance>` of this service.

    .. method:: __len__()

        Returns the number of known instances of this service.


.. class:: ServiceInstance()

    Normally created by :meth:`ServiceContainer.lookup() <lymph.core.container.ServiceContainer.lookup()>`

    .. method:: connect()

        :return: :class:`lymph.core.connection.Connection` to this service instance

    .. method:: disconnect()

        Disconnects from this service instance.


.. currentmodule:: lymph.core.connections

.. class:: Connection

    You can attain a connection to an lymph service instance directly from :meth:`lymph.core.container.ServiceContainer.connect`, or
    from the higher-level API in :mod:`lymph.core.services`.
    For ZeroMQ endpoint addresses the following to statements are roughly equivalent::

        container.connect(address)  # only works for tcp://… addresses
        container.lookup(address).connect()  # will also work for lymph://… addresses


