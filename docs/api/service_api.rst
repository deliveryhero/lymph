.. currentmodule:: lymph

Service API
===========

::

    import lymph


    class Echo(lymph.Interface):
        service_type = 'echo'

        @lymph.rpc()
        def echo(self, text=None):
            return text

        @lymph.rpc()
        def upper(self, text=None):
            self.emit('uppercase_transform_finished', {'text': text})
            return text.upper()

        @lymph.event('uppercase_transform_finished')
        def on_uppercase(self, text=None):
            print "done", text


.. class:: Interface

    .. attribute:: service_type

        The service identifier that is used to register this service with the coordinator service.
        ``service_type`` is usually set as a class attribute.

    .. method:: on_start()

        Called when the service is started


    .. method:: on_stop()

        Called when the service is stopped

    .. method:: apply_config(config)

        :param config: dict

        Called with instance specific configuration that is usually provided by a
        config file (see :ref:`interface-config`).


    .. method:: request(address, method, body)

        :param address: the address where the request is sent to; either a ZeroMQ endpoint or a service name
        :param method: the remote method that will be called
        :param body: JSON serializable dict of parameters for the remote method


    .. method:: proxy(address)

        returns a proxy object that can be used to conveniently send requests to
        another service.

        .. code-block:: python

            echo = self.proxy('echo')
            result = echo.upper(text='foo')
            assert result == 'FOO'

        This is equivalent to ``self.request('echo', 'echo.upper', text='foo')``.


    .. method:: emit(event_type, payload)

        :param event_type: str
        :param payload: a dict of JSON serializable data structures

    .. decorator:: subscribe(*event_types, sequential=True)

        Behaves like :func:`lymph.event`, but can be used at runtime

        .. code::

            class Example(lymph.Service):
                def on_start(self):
                    @self.subscribe('dynamic_event_type')
                    def on_event(event):
                        assert isinstance(event, lymph.core.events.Event)


.. decorator:: raw_rpc()

    Marks the decorated interface method as an RPC method. Using this decorator
    the RPC function are expected to accept a :class:`ReplyChannel` instance
    as a first argument.

    .. code::

        import lymph

        class Example(lymph.Interface):
            @lymph.raw_rpc()
            def do_something(self, channel, message):
                assert isinstance(channel, lymph.core.channels.ReplyChannel)
                assert isinstance(message, lymph.core.messages.Message)
                channel.ack()

.. decorator:: rpc()

    Marks the decorated interface method as an RPC method. The difference between
    this decorator and :func:`raw_rpc` is that the RPC functions must use
    return and raise like any normal Python function instead of using ``channel.reply``
    and ``channel.error``.

    :param raises: tuple of exception classes that the RPC function is expected to raise.

    .. code::

        import lymph

        class Example(lymph.Interface):
            @lymph.rpc()
            def do_something(self, message):
                return message


.. decorator:: event(*event_types, sequential=False)

    :param event_types: may contain wildcards, e.g. ``'subject.*'``
    :param sequential: force sequential event consumption

    Marks the decorated interface method as an event handler.
    The service container will automatically subscribe to given ``event_types``.
    If ``sequential=True``, events will be not be consumed in parallel, but one by one.

    .. code::

        import lymph

        class Example(lymph.Interface):
            @lymph.event('task_done')
            def on_task_done(self, event):
                assert isinstance(event, lymph.core.events.Event)
