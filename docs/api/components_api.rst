.. currentmodule:: lymph.core.components


Components API
==============

Components are objects that depend on a running service container. They are
embedded in :class:`Componentized` objects.
Since Componentized objects themselves are components, they form a tree of
:class:`Component` instances with the container as the root. An example
of a Component is :class:`lymph.core.interfaces.Interface`.


.. class:: Component(error_hook=None, pool=None, metrics=None)

    .. attribute:: error_hook

        A Hook object that propagates exceptions for this component.
        Defaults to the ``error_hook`` of the parent component.

    .. attribute:: pool

        A pool that holds greenlets related to the component.
        Defaults to the ``pool`` of the parent component.

    .. attribute:: metrics

        An :class:`Aggregate <lymph.core.monitoring.metrics.Aggregate>` of metrics for this component.
        Defaults to the ``metrics`` of the parent component.

    .. method:: on_start()

        Called when the container is started.

    .. method:: on_stop()

        Called when the container is stopped.

    .. method:: spawn(func, *args, **kwargs)

        Spawns a new greenlet in the greenlet pool of this component.
        If ``func`` exits with an exception, it is reported to the ``error_hook``.


.. class:: Componentized()

    A collection of components; itself a component.

    .. method:: add_component(component)

        :param component: :class:`Component`

        Adds `component`.

    .. method:: on_start()

        Calls `on_start()` on all added components.

    .. method:: on_stop()

        Calls `on_stop()` on all added components.
