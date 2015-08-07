from lymph.core.monitoring.metrics import Aggregate
from lymph.core.monitoring.global_metrics import RUsageMetrics, GeventMetrics, GarbageCollectionMetrics, ProcessMetrics


class Aggregator(Aggregate):
    @classmethod
    def from_config(cls, config):
        tags = config.get_raw('tags', {})
        # FIXME: move default metrics out
        return cls([
            RUsageMetrics(),
            GarbageCollectionMetrics(),
            GeventMetrics(),
            ProcessMetrics(),
        ], tags=tags)
