import unittest

from lymph.core.monitoring.metrics import Gauge
from lymph.core.monitoring.aggregator import Aggregator


class AggregatorTestCase(unittest.TestCase):

    def test_aggregator_one_component(self):
        aggr = Aggregator([Gauge('dummy', 'one')])

        self.assertIn(('dummy', 'one', {}), list(aggr))

    def test_aggregator_multiple_components(self):
        aggr = Aggregator([
            Gauge('dummy', 'one'),
            Gauge('dummy', 'two')
        ], tags={'name': 'test'})

        self.assertIn(('dummy', 'one', {'name': 'test'}), list(aggr))
        self.assertIn(('dummy', 'two', {'name': 'test'}), list(aggr))

    def test_aggregator_add_multiple_tags(self):
        aggr = Aggregator([
            Gauge('dummy', 'one')
        ], tags={'name': 'test'})

        aggr.add_tags(origin='localhost', time='now')

        self.assertIn(('dummy', 'one', {'name': 'test', 'origin': 'localhost', 'time': 'now'}), list(aggr))
