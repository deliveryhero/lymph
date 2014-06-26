from unittest import TestCase

from lymph.utils import import_object, Undefined


class ImportTests(TestCase):

    def test_import_object(self):
        from lymph.core.container import ServiceContainer
        cls = import_object('lymph.core.container:ServiceContainer')
        self.assertIs(cls, ServiceContainer)

    def test_import_object_without_colon(self):
        self.assertRaises(ValueError, import_object, 'lymph.core.container.ServiceContainer')
        self.assertRaises(ValueError, import_object, 'lymph.core.container')


class UndefinedTests(TestCase):
    def test_properties(self):
        self.assertNotEqual(Undefined, None)
        self.assertNotEqual(Undefined, False)
        self.assertFalse(bool(Undefined))
        self.assertEqual(str(Undefined), 'Undefined')
