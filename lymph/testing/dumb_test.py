__author__ = 'mislavstipetic'

from lymph.testing import APITestCase
from dhh.api.interfaces import DeliveryHeroApi


class OnceTest(APITestCase):
    test_interface = DeliveryHeroApi

    def dumb_test(self):
        resp = self.client.get("/")
        print resp.data
        print "DUBM"