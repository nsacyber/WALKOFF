import unittest

from apps.decorators import *


class TestDecorators(unittest.TestCase):
    def test_action_decorator_is_tagged(self):
        @action
        def add_three(a, b, c):
            return a + b + c

        self.assertTrue(getattr(add_three, 'action'))

    def test_action_decorator_has_arg_names(self):
        @action
        def add_three(a, b, c):
            return a + b + c

        self.assertListEqual(getattr(add_three, '__arg_names'), ['a', 'b', 'c'])

    def test_action_wraps_execution_return_not_specified(self):
        @action
        def add_three(a, b, c):
            return a + b + c

        self.assertEqual(add_three(1, 2, 3), ActionResult(6, None))

    def test_action_wraps_execution_return_specified(self):
        @action
        def add_three(a, b, c):
            return a + b + c, 'Custom'

        self.assertEqual(add_three(1, 2, 3), ActionResult(6, 'Custom'))

    def test_flag_decorator_is_tagged(self):
        @condition
        def is_even(x):
            return x % 2 == 0

        self.assertTrue(getattr(is_even, 'condition'))
        self.assertTrue(is_even(2))

    def test_filter_decorator_is_tagged(self):
        @transform
        def add_one(x):
            return x + 1

        self.assertTrue(getattr(add_one, 'transform'))
        self.assertEqual(add_one(1), 2)
