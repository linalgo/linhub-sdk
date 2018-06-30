import unittest

from linalgo.client import LinalgoClient
import os


class TestSDK(unittest.TestCase):

    def setUp(self):
        token = os.environ.get('ACCESS_TOKEN', None)
        if token is not None:
            self.client = LinalgoClient(token)
        else:
            raise Exception("Please set access token for testing!")

    def test_auth(self):
        self.assertTrue(self.client.authenticate())


if __name__ == '__main__':
    unittest.main()
