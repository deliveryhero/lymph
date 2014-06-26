.. currentmodule:: lymph

Service API
===========

::

    import lymph


    class Echo(lymph.Interface):
        service_type = 'echo'

        @lymph.rpc()
        def echo(self, channel, text=None):
            channel.reply(text)

        @lymph.rpc()
        def upper(self, channel, text=None):
            channel.reply(text.upper())
            self.emit('uppercase_transform_finished', {'text': text})

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

        :param address: the address where the request is sent to; either a ZeroMQ endpoint or an lymph:// url
        :param method: the remote method that will be called
        :param body: JSON serializable dict of parameters for the remote method


    .. method:: proxy(address)

        returns a proxy object that can be used to conveniently send requests to
        another service.

        .. code-block:: python

            echo = self.proxy('lymph://echo')
            result = echo.upper(text='foo')
            assert result == 'FOO'

        This is equivalent to ``self.request('lymph://echo', 'echo.upper', text='foo')``.


    .. method:: emit(event_type, payload)

        :param event_type: str
        :param payload: a dict of JSON serializable data structures


.. decorator:: rpc( )

    marks the decorated method as remotely callable


.. decorator:: event(event_type)

    the decorated method will be called when the service receives an event of the given ``event_type``.
    The ``payload`` dict that was passed to :meth:`Service.emit()` will be passed as keyword arguments.


.. class:: Proxy(container, address, namespace=None, timeout=1)

    .. method:: __getattr__(self, name)

        Returns a callable that will execute the RPC method with the given name.


