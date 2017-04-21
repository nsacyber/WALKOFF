from apps.HelloWorld import display
from werkzeug.wsgi import ClosingIterator
from tests.util.servertestcase import ServerTestCase


class TestDisplay(ServerTestCase):

    def test_load(self):
        self.assertDictEqual(display.load(), {})

    def test_stream_counter(self):
        response = self.app.get('/apps/HelloWorld/stream/counter', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.response, ClosingIterator)

    def test_stream_random_number(self):
        response = self.app.get('/apps/HelloWorld/stream/random-number', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.response, ClosingIterator)
