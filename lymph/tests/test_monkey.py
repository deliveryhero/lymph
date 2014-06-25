import unittest


class InitializeTest(unittest.TestCase):

    def test_assure_that_lymph_is_initialized_by_testrunner(self):
        import lymph.monkey
        self.assertTrue(lymph.monkey.patch._initialized)
