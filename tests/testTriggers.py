import unittest
from server import server


class TestTriggers(unittest.TestCase):
    def setUp(self):
        self.app = server.app.test_client(self)
        self.app.testing = True
        response = self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)

    def test_grep(self):
        print('Not Implemented!')
