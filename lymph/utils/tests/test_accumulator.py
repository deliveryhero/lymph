from __future__ import division

from six.moves import range
from unittest import TestCase

from lymph.utils import Accumulator


class AccumulatorTests(TestCase):
    def test_accumulator(self):
        acc = Accumulator()
        for i in range(1, 6):
            acc.add(i / 15.)
        self.assertEqual(acc.n, 5)
        self.assertEqual(acc.sum, 1)
        self.assertEqual(acc.mean, 0.2)
        self.assertEqual(acc.stddev, 0.09428090415820631)
