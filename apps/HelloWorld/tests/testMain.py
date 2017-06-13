from unittest import TestCase
from apps.HelloWorld import main
import time


class TestMain(TestCase):
    def setUp(self):
        self.app = main.Main()

    def test_hello_world(self):
        message = self.app.helloWorld()
        self.assertDictEqual(message, {"message": "HELLO WORLD"})

    def test_repeat_to_me(self):
        self.assertEqual(self.app.repeatBackToMe('test_message'), 'REPEATING: {0}'.format('test_message'))

    def test_plus_one(self):
        self.assertEqual(self.app.returnPlusOne(4), 5)
        with self.assertRaises(ValueError):
            self.app.returnPlusOne('aa')

    def test_pause(self):
        start = time.time()
        self.app.pause(1)
        end = time.time()
        self.assertAlmostEqual(end-start, 1.0, 2)

    def test_shutdown(self):
        self.assertIsNone(self.app.shutdown())
