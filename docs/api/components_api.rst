.. currentmodule:: lymph.core.components


Components API
==============

Components are objects that depend on a running service container. They are 
embedded in :class:`Componentized` objects. 
Since Componentized objects themselves are components, they form a tree of 
:class:`Component` instances with the container as the root.


.. class:: Component

    .. attribute:: metrics
    
        A :class:`Metrics` instance that will be included in the monitoring data
        of the conatainer.

    .. method:: on_start()
    
        Called when the container is started.

    .. method:: on_stop()
    
        Called when the container is stopped.


.. class:: Componentized()

    A collection of components; itself a component.

    .. method:: add_component(component)
    
        :param component: :class:`Component`
    
        Adds `component`.
    
    .. attribute:: metrics
    
        A :class:`Metrics` instance that aggregates the metrics from all added components.
    
    .. method:: on_start()
    
        Calls `on_start()` on all added components.
    
    .. method:: on_stop()

        Calls `on_stop()` on all added components.
