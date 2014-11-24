from lymph.testing import APITestCase
from dhh.api.interfaces import DeliveryHeroApi

class BasicTest(APITestCase):

    test_interface = DeliveryHeroApi

    def get_root(self):
        print self.client.get("/")