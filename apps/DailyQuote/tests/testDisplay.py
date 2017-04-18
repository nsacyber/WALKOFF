from unittest import TestCase
from apps.DailyQuote import display


class TestDisplay(TestCase):

    def test_load(self):
        self.assertDictEqual(display.load(), {})
