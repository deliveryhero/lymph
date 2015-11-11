.. currentmodule:: lymph.core.monitoring.metrics


Metrics API
===========

To follow the metrics protocol objects must be iterable repeatedly and yield
``(name, value, tags)``-triples, where ``name`` is a string, ``value`` is a float or int,
and ``tags`` is a dict with string keys and values.


.. class:: Metric(name, tags=None)

   An abstract base class for single series metrics, i.e. metric objects that
   only yield a single triple.

   .. method:: __iter__()

      **[abstract]** Yields metric values as a tuple in the form
      `(name, value, tags)`.


.. class:: Gauge(name, value=0, tags=None)

    A gauge is a metric that represents a single numerical value that can
    arbitrarily go up and down.

    .. method:: set(value)


.. class:: Callable(name, func, tags=None)

    Like a Gauge metric, but its value is determined by a callable.


.. class:: Counter(name, tags=None)

    A counter is a cumulative metric that represents a single numerical
    value that only ever goes up. A counter is typically used to count
    requests served, tasks completed, errors occurred, etc.

    .. method:: __iadd__(value)

      Increment counter value.


.. class:: TaggedCounter(name, tags=None)

    A tagged counter is a container metric that represents multiple
    counters per tags. A tagged counter is typically used to track a group
    of counters as one e.g. request served per function name, errors ocurred
    per exception name, etc.

    .. method:: incr(_by=1, **tags)

      Increment given counter ``type`` by ``_by``.


.. class:: Aggregate(metrics=(), tags=None)

    :param metrics: iterable of metric objects
    :param tags: dict of tags to add to all metrics.

    Aggregates a collection of metrics into a single metrics object.

    .. method:: add(metric)
    
        :param metric: metric object
    
        Adds the given metric to collection.

    .. method:: add_tags(**tags)
    
        :param tags: string-valued dict

        Adds the given tags for all metrics.
