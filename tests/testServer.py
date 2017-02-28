import unittest

from server import flaskServer as server


class TestLogin(unittest.TestCase):
    def setUp(self):
        self.app = server.app.test_client(self)
        self.app.testing = True
        response = self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)

    def test_login(self):
        response = self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)

