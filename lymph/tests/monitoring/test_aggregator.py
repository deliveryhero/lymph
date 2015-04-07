import unittest

from lymph.core.monitoring.metrics import RawMetric
from lymph.core.monitoring.aggregator import Aggregator


def _get_metrics_one(self):
    yield RawMetric('dummy', 'one')


def _get_metrics_two(self):
    yield RawMetric('dummy', 'two')


class AggregatorTestCase(object):

    def test_aggregator_one_component(self):
        aggr = Aggregator(_get_metrics_one, name='test')

        self.assertEqual(list(aggr.get_metrics()), [('dummy', 'one', {'name': 'test'})])

    def test_aggregator_multiple_components(self):
        aggr = Aggregator(_get_metrics_one, _get_metrics_two, name='test')

        self.assertEqual(list(aggr.get_metrics()), [
            ('dummy', 'one', {'name': 'test'}),
            ('dummy', 'two', {'name': 'test'}),
        ])

    def test_aggregator_add_multiple_tags(self):
        aggr = Aggregator(_get_metrics_one, name='test')

        aggr.add_tags(origin='localhost', time='now')

        self.assertEqual(list(aggr.get_metrics()), [
            ('dummy', 'one', {'name': 'test', 'origin': 'localhost', 'time': 'now'})
        ])
