.. currentmodule:: lymph.patterns

Pattern API
===========

.. currentmodule:: lymph.patterns.partitioned_event

.. decorator:: partitioned_event(*event_types, partition_count=12, key=None)

    :param event_types: event types that should be partitioned
    :param partition_count: number of queues that should be used to partition the events
    :param key: a function that maps :class:`Events <lymph.core.events.Event>` to string keys
    
    This event handler redistributes events into ``partition_count`` queues. 
    These queues are then partitioned over all service instances and consumed sequentially, 
    i.e. at most one event per queue at a time.
    