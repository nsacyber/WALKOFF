from unittest import TestCase
from apps.DailyQuote import display
from types import GeneratorType


class TestDisplay(TestCase):

    def test_load(self):
        self.assertDictEqual(display.load(), {})

    # def testQuote(self):
    #     self.assertDictEqual()