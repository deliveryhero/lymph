import unittest

from lymph.core.monitoring.metrics import RawMetric
from lymph.core.monitoring.aggregator import Aggregator


def _get_metrics_one():
    yield RawMetric('dummy', 'one')


def _get_metrics_two():
    yield RawMetric('dummy', 'two')


class AggregatorTestCase(unittest.TestCase):

    def test_aggregator_one_component(self):
        aggr = Aggregator(_get_metrics_one, name='test')

        self.assertIn(('dummy', 'one', {'name': 'test'}), list(aggr.get_metrics()))

    def test_aggregator_multiple_components(self):
        aggr = Aggregator(_get_metrics_one, _get_metrics_two, name='test')

        self.assertIn(('dummy', 'one', {'name': 'test'}), list(aggr.get_metrics()))
        self.assertIn(('dummy', 'two', {'name': 'test'}), list(aggr.get_metrics()))

    def test_aggregator_add_multiple_tags(self):
        aggr = Aggregator(_get_metrics_one, name='test')

        aggr.add_tags(origin='localhost', time='now')

        self.assertIn(('dummy', 'one', {'name': 'test', 'origin': 'localhost', 'time': 'now'}), list(aggr.get_metrics()))
