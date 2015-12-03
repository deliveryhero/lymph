import lymph
from lymph.core.interfaces import Interface
from lymph.testing import MultiServiceRPCTestCase
from lymph.exceptions import NotConnected


class Foo(Interface):
    @lymph.rpc()
    def get_class_name(self):
        return self.__class__.__name__


class Foo11(Foo):
    pass


class Foo12(Foo):
    pass


class Foo15(Foo):
    pass


class Foo21(Foo):
    pass


class Foo33(Foo):
    pass


class VersionedRpcTests(MultiServiceRPCTestCase):
    containers = [
        {
            'foo@1.1': {'class': Foo11},
            'foo@1.5': {'class': Foo15},
            'foo@2.1': {'class': Foo21},
        },
        {
            'foo@1.2': {'class': Foo12},
            'foo@3.3': {'class': Foo33},
            'foo@4.0': {'class': Foo33},  # interface classes can be reused
        }
    ]

    def test_version_matching(self):
        proxy = self.client.proxy('foo', version='1.1')
        self.assertIn(proxy.get_class_name(), {'Foo11', 'Foo12', 'Foo15'})

        proxy = self.client.proxy('foo', version='1.2')
        self.assertIn(proxy.get_class_name(), {'Foo12', 'Foo15'})

        proxy = self.client.proxy('foo', version='1.7')
        self.assertRaises(NotConnected, proxy.get_class_name)

        proxy = self.client.proxy('foo', version='2.0')
        self.assertIn(proxy.get_class_name(), {'Foo21'})

        proxy = self.client.proxy('foo', version='2.5')
        self.assertRaises(NotConnected, proxy.get_class_name)

        proxy = self.client.proxy('foo', version='4.0')
        self.assertIn(proxy.get_class_name(), {'Foo33'})


class UnversionedRpcTests(MultiServiceRPCTestCase):
    containers = [
        {
            'foo@1.5': {'class': Foo15},
            'foo': {'class': Foo11},
        },
        {
            'foo@1.2': {'class': Foo12},
        }
    ]

    def test_unversioned(self):
        proxy = self.client.proxy('foo')
        self.assertIn(proxy.get_class_name(), {'Foo11', 'Foo15', 'Foo12'})

