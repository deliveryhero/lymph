.. currentmodule:: lymph.core.components


Components API
==============

Components are objects that depend on a running service container. They are
embedded in :class:`Componentized` objects.
Since Componentized objects themselves are components, they form a tree of
:class:`Component` instances with the container as the root. An example
of a Component is :class:`lymph.core.interfaces.Interface`.


.. class:: Component

    .. method:: on_start()

        Called when the container is started.

    .. method:: on_stop()

        Called when the container is stopped.

    .. method:: _get_metrics()

        Is being called to get metrics. Returns an iterable or yields
        values of type :class:`lymph.core.monitoring.metrics.RawMetric`.


.. class:: Componentized()

    A collection of components; itself a component.

    .. method:: add_component(component)

        :param component: :class:`Component`

        Adds `component`.

    .. method:: on_start()

        Calls `on_start()` on all added components.

    .. method:: on_stop()

        Calls `on_stop()` on all added components.
