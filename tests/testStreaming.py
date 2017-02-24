import unittest
import json
from werkzeug.wsgi import ClosingIterator
from server import flaskServer as flask_server


class TestStreaming(unittest.TestCase):

    def setUp(self):
        self.app = flask_server.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        response = self.app.post('/key', data=dict(email='admin', password='admin'),
                                 follow_redirects=True).get_data(as_text=True)

        self.key = json.loads(response)["auth_token"]
        self.headers = {"Authentication-Token": self.key}

    def test_stream_from_server(self):
        response = self.app.get('/apps/HelloWorld/stream/counter', headers=self.headers)
        self.assertEquals(response.status_code, 200)
        self.assertIsInstance(response.response, ClosingIterator)
        response = self.app.get('/apps/HelloWorld/stream/random-number', headers=self.headers)
        self.assertEquals(response.status_code, 200)
        self.assertIsInstance(response.response, ClosingIterator)
