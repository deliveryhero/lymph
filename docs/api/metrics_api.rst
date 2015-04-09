.. currentmodule:: lymph.core.monitoring.metrics


Metrics API
===========


.. class:: RawMetric(name, value, tags=None)

   Raw metric that represent an arbitrary value a.k.a Gauge Metric.

   .. method:: __iter__()

      Yield metric values as a tuple in the form `(name, value, tags)`.


.. class:: Counter(name, tags=None)

    A counter is a cumulative metric that represents a single numerical
    value that only ever goes up. A counter is typically used to count
    requests served, tasks completed, errors occurred, etc.

    .. method:: __iadd__(new_value=1)

      Increment counter value.


.. class:: TaggedCounter(name, tags=None)

    A tagged counter is a container metric that represents multiple
    counters per tags. A tagged counter is typically used to track a group
    of counters as one e.g. request served per function name, errors ocurred
    per exception name, etc.

    .. method:: incr(_value=1, **tags)

      Increment given counter ``type`` by ``new_value``.
