import unittest
from core.decorators import *

class TestDecorators(unittest.TestCase):

    def test_action_decorator(self):

        @action
        def add_three(a,  b, c):
            return a+b+c

        self.assertTrue(getattr(add_three, 'action'))
        self.assertEqual(add_three(1, 2, 3), 6)

    def test_flag_decorator(self):

        @flag
        def is_even(x):
            return x % 2 == 0

        self.assertTrue(getattr(is_even, 'flag'))
        self.assertTrue(is_even(2))

    def test_filter_decorator(self):
        @datafilter
        def add_one(x):
            return x+1

        self.assertTrue(getattr(add_one, 'filter'))
        self.assertEqual(add_one(1), 2)
