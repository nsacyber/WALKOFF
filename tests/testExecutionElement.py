import unittest

from core.executionelement import ExecutionElement


class TestExecutionElement(unittest.TestCase):

    def test_init(self):
        elem = ExecutionElement()
        self.assertEqual(elem.name, '')
        self.assertEqual(elem.parent_name, '')

        elem = ExecutionElement(name='test')
        self.assertEqual(elem.name, 'test')
        self.assertEqual(elem.parent_name, '')

        elem = ExecutionElement(parent_name='parent_test')
        self.assertEqual(elem.name, '')
        self.assertEqual(elem.parent_name, 'parent_test')

        elem = ExecutionElement(ancestry=['a', 'b', 'c'])
        self.assertEqual(elem.name, '')
        self.assertEqual(elem.parent_name, '')

    def test_construct_ancestry(self):
        elem = ExecutionElement()
        self.assertListEqual(elem.ancestry, ['', ''])

        elem = ExecutionElement(name='test')
        self.assertListEqual(elem.ancestry, ['', 'test'])

        elem = ExecutionElement(parent_name='parent_test')
        self.assertListEqual(elem.ancestry, ['parent_test', ''])

        elem = ExecutionElement(ancestry=['a', 'b', 'c'])
        self.assertListEqual(elem.ancestry, ['a', 'b', 'c', ''])

        elem = ExecutionElement(ancestry=['a', 'b', 'c'], name='d')
        self.assertListEqual(elem.ancestry, ['a', 'b', 'c', 'd'])

        elem = ExecutionElement(ancestry=['a', 'b', 'c'], parent_name='d')
        self.assertListEqual(elem.ancestry, ['a', 'b', 'c', ''])

        elem = ExecutionElement(ancestry=['a', 'b', 'c'], parent_name='d', name='e')
        self.assertListEqual(elem.ancestry, ['a', 'b', 'c', 'e'])
