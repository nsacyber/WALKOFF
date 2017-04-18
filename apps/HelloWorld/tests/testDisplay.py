from unittest import TestCase
from apps.HelloWorld import display
from types import GeneratorType


class TestDisplay(TestCase):

    def test_load(self):
        self.assertDictEqual(display.load(), {})

    def __check_num_stream(self, stream):
        self.assertTrue(stream.startswith('data: '))
        self.assertTrue(stream.endswith('\n\n'))

    def test_counter_stream(self):
        counter, mimetype = display.stream_generator('counter')
        self.assertEqual(mimetype, 'text/event-stream')
        self.assertTrue(callable(counter))
        self.assertIsInstance(counter(), GeneratorType)
        counter = counter()
        for i in range(3):
            stream_num = next(counter)
            self.__check_num_stream(stream_num)
            separated = stream_num.split(':')
            self.assertEqual(len(separated), 2)
            self.assertEqual(int(separated[1]), i)

    def test_random_stream(self):
        random, mimetype = display.stream_generator('random-number')
        self.assertEqual(mimetype, 'text/event-stream')
        self.assertTrue(callable(random))
        self.assertIsInstance(random(), GeneratorType)
        random = random()
        for _ in range(3):
            stream_num = next(random)
            self.__check_num_stream(stream_num)
            separated = stream_num.split(':')
            self.assertEqual(len(separated), 2)
            num = float(separated[1])
            self.assertGreaterEqual(num, 0.0)
            self.assertLess(num, 1.0)
