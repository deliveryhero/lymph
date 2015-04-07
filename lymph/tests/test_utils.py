import unittest

import gevent

from lymph.utils import gpool


def some_work():
    pass


class NonBlockingPoolTestCase(unittest.TestCase):

    def setUp(self):
        self.pool = gpool.NonBlockingPool(size=2)

    def test_full_pool_status(self):
        self.pool.spawn(some_work)
        self.pool.spawn(some_work)

        self.assertTrue(self.pool.full())
        self.assertEqual(self.pool.free_count(), 0)

    def test_spawn_on_full_pool_should_fail(self):
        self.pool.spawn(some_work)
        self.pool.spawn(some_work)

        with self.assertRaises(gpool.RejectExcecutionError):
            self.pool.spawn(some_work)

    def test_finished_work_should_freeup_resources_from_pool(self):
        self.pool.spawn(some_work)

        gevent.wait(self.pool)

        self.assertEqual(self.pool.free_count(), 2)
