import unittest


class InitializeTest(unittest.TestCase):

    def test_assure_that_iris_is_initialized_by_testrunner(self):
        import iris.monkey
        self.assertTrue(iris.monkey.patch._initialized)
