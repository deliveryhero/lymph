from unittest import TestCase

from lymph.utils.sockets import guess_external_ip


class SocketUtilsTests(TestCase):
    def test_guess_external_ip(self):
        self.assertNotEqual(guess_external_ip(), '127.0.0.1')
