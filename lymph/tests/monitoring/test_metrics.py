import operator
import unittest

from lymph.core.monitoring import metrics


class RawMetricsTest(unittest.TestCase):

    def test_repr(self):
        raw = metrics.RawMetric('raw', 'foobar', {})

        self.assertEqual(repr(raw), "RawMetric(name='raw', value='foobar', tags={})")

    def test_iter(self):
        raw = metrics.RawMetric('raw', 'foobar', {})

        self.assertEqual(list(raw), [('raw', 'foobar', {})])


class CounterMetricsTest(unittest.TestCase):

    def test_get(self):
        counter = metrics.Counter('requests')

        self.assertEqual(list(counter), [('requests', 0, {})])

    def test_repr(self):
        counter = metrics.Counter('requests')

        self.assertEqual(str(counter), repr(counter))
        self.assertEqual(repr(counter), "Counter(name='requests', value=0, tags={})")

    def test_increment_by_one(self):
        counter = metrics.Counter('requests')
        counter += 1

        self.assertEqual(list(counter), [('requests', 1, {})])

    def test_increment_by_many(self):
        counter = metrics.Counter('requests')
        counter += 66

        self.assertEqual(list(counter), [('requests', 66, {})])


class TaggedCounterMetricsTest(unittest.TestCase):

    def test_incr_one_type(self):
        error_counter = metrics.TaggedCounter('exception')

        error_counter.incr(type='ValueError')
        error_counter.incr(4, type='ValueError')

        self.assertEqual(list(error_counter), [
            ('exception', 5, {'type': 'ValueError'})])

    def test_incr_different_types(self):
        error_counter = metrics.TaggedCounter('exception')

        error_counter.incr(type='ValueError')
        error_counter.incr(type='ValueError')

        error_counter.incr(type='Nack')

        self.assertEqual(
            sorted(error_counter, key=operator.itemgetter(1)), [
                ('exception', 1, {'type': 'Nack'}),
                ('exception', 2, {'type': 'ValueError'}),
            ])
