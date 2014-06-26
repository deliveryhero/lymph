
import logging
from unittest import TestCase

from lymph.utils.logging import get_loglevel


class LoggingUtilsTests(TestCase):
    def test_get_loglevel(self):
        self.assertEqual(get_loglevel('DEBUG'), logging.DEBUG)
        self.assertEqual(get_loglevel('debug'), logging.DEBUG)
        self.assertEqual(get_loglevel('Debug'), logging.DEBUG)
        self.assertEqual(get_loglevel('INFO'), logging.INFO)
        self.assertEqual(get_loglevel('info'), logging.INFO)
        self.assertEqual(get_loglevel('ERROR'), logging.ERROR)
        self.assertEqual(get_loglevel('error'), logging.ERROR)
        self.assertEqual(get_loglevel('CRITICAL'), logging.CRITICAL)
        self.assertEqual(get_loglevel('critical'), logging.CRITICAL)

        self.assertRaises(ValueError, get_loglevel, 'FOO')
        self.assertRaises(ValueError, get_loglevel, '*')
