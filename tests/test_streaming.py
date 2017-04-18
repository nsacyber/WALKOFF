from werkzeug.wsgi import ClosingIterator
from tests.util.servertestcase import ServerTestCase


class TestStreaming(ServerTestCase):

    def test_stream_from_server(self):
        response = self.app.get('/apps/HelloWorld/stream/counter', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.response, ClosingIterator)
        response = self.app.get('/apps/HelloWorld/stream/random-number', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.response, ClosingIterator)
