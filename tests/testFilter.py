import unittest
import sys
from core.filter import Filter


class TestFilter(unittest.TestCase):
    def compare_init(self, elem, action, parent_name, ancestry, args=None):
        args = args if args is not None else {}
        self.assertEqual(elem.action, action)
        self.assertDictEqual({arg_name: arg_value.as_json() for arg_name, arg_value in elem.args.items()}, args)
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

        args = {'arg1': 'a', 'arg2': 3, 'arg3': u'abc'}
        expected_args_json = {'arg1': {'key': 'arg1', 'value': 'a', 'format': 'str'},
                              'arg2': {'key': 'arg2', 'value': '3', 'format': 'int'}}

        if sys.version_info < (3, 0):
            expected_args_json['arg3'] = {'key': 'arg3', 'value': 'abc', 'format': 'unicode'}
        else:
            expected_args_json['arg3'] = {'key': 'arg3', 'value': 'abc', 'format': 'str'}

        filter = Filter(ancestry=['a', 'b'], action="test", args=args)
        self.compare_init(filter, 'test', '', ['a', 'b', 'test'], args=expected_args_json)

    def test_as_json(self):
        filter = Filter()
        self.assertDictEqual(filter.as_json(), {'action': '', 'args': {}})

        filter = Filter(action='test_action')
        self.assertDictEqual(filter.as_json(), {'action': 'test_action', 'args': {}})

        args = {'arg1': 'a', 'arg2': 3, 'arg3': u'abc'}
        expected_args_json = {'arg1': {'key': 'arg1', 'value': 'a', 'format': 'str'},
                              'arg2': {'key': 'arg2', 'value': '3', 'format': 'int'}}
        if sys.version_info < (3, 0):
            expected_args_json['arg3'] = {'key': 'arg3', 'value': 'abc', 'format': 'unicode'}
        else:
            expected_args_json['arg3'] = {'key': 'arg3', 'value': 'abc', 'format': 'str'}

        expected_filter_json = {'action':  'test', 'args': expected_args_json}
        filter = Filter(ancestry=['a', 'b'], action="test", args=args)
        self.assertDictEqual(filter.as_json(), expected_filter_json)

    def test_from_json(self):
        args = {'arg1': 'a', 'arg2': 3, 'arg3': u'abc'}
        input_output = {Filter(): ('', ['']),
                        Filter(action='test_action'): ('', ['']),
                        Filter(action='test_action', parent_name='test_parent'):
                            ('test_parent', ['test_parent']),
                        Filter(ancestry=['a', 'b'], action="test", args=args): ('', ['a', 'b'])}
        for filter_element, (parent_name, ancestry) in input_output.items():
            filter_json = filter_element.as_json()
            derived_filter = Filter.from_json(filter_json, parent_name=parent_name, ancestry=ancestry)
            self.assertDictEqual(derived_filter.as_json(), filter_json)
            self.assertEqual(filter_element.parent_name, derived_filter.parent_name)
            self.assertListEqual(filter_element.ancestry, derived_filter.ancestry)

    def test_to_from_xml(self):
        args = {'arg1': 'a', 'arg2': 3, 'arg3': u'abc'}
        input_output = [Filter(), Filter(action='test_action'), Filter(ancestry=['a', 'b'], action="test", args=args)]

        for filter_element in input_output:
            original_json = filter_element.as_json()
            derived_json = Filter(xml=filter_element.to_xml()).as_json()
            self.assertEqual(original_json, derived_json)

    def test_invalid_filter(self):
        filter = Filter(action='junkAction')
        self.assertIsNone(filter())
        self.assertEqual(filter(output=6), 6)

    def test_length_filter(self):
        filter = Filter(action='length')
        self.assertIsNone(filter())
        self.assertEqual(filter(output=6), 6)
        self.assertEqual(filter(output=5.5), None)
        self.assertEqual(filter(output=[3,4,5]), 3)
        self.assertEqual(filter(output='aaab'), 4)