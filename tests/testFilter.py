import unittest

from core.filter import Filter
from core.executionelement import ExecutionElement


class TestFilter(unittest.TestCase):

    def compare_init(self, elem, action, parent_name, ancestry, args=None):
        args = args if args is not None else {}
        self.assertEqual(elem.action, action)
        self.assertDictEqual(elem.args, args)
        self.assertEqual(elem.name, elem.action)
        self.assertEqual(elem.parent_name, parent_name)
        self.assertListEqual(elem.ancestry, ancestry)
        self.assertEqual(elem.event_handler.event_type, 'FilterEventHandler')

    def test_init(self):
        filter = Filter()
        self.compare_init(filter, '', '', ['', ''])

        filter = Filter(action='test_action')
        self.compare_init(filter, 'test_action', '', ['', 'test_action'])

        filter = Filter(parent_name='test_parent', action='test_action')
        self.compare_init(filter, 'test_action', 'test_parent', ['test_parent', 'test_action'])

        filter = Filter(ancestry=['a', 'b'], action="test")
        self.compare_init(filter, 'test', '', ['a', 'b', 'test'])