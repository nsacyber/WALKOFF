import unittest
import sys
import copy
from core.filter import Filter
from core import config


class TestFilter(unittest.TestCase):
    def setUp(self):
        self.original_functions = copy.deepcopy(config.functionConfig)
        self.test_funcs = {'filters': {'func_name1': {'args': []},
                                       'func_name2': {'args': [{'name': 'arg_name1', 'type': 'str'}]},
                                       'func_name3': {'args': [{'name': 'arg_name1', 'type': 'str'},
                                                               {'name': 'arg_name2', 'type': 'int'}]}}}
        for func_name, arg_dict in self.test_funcs['filters'].items():
            config.functionConfig['filters'][func_name] = arg_dict

    def tearDown(self):
        config.functionConfig = self.original_functions

    def compare_init(self, elem, action, parent_name, ancestry, args=None):
        args = args if args is not None else {}
        self.assertEqual(elem.action, action)
        self.assertDictEqual({arg_name: arg_value.as_json() for arg_name, arg_value in elem.args.items()}, args)
        self.assertEqual(elem.name, elem.action)
        self.assertEqual(elem.parent_name, parent_name)
        self.assertListEqual(elem.ancestry, ancestry)
        self.assertEqual(elem.event_handler.event_type, 'FilterEventHandler')

    def test_init(self):
        filter_elem = Filter()
        self.compare_init(filter_elem, '', '', ['', ''])

        filter_elem = Filter(action='test_action')
        self.compare_init(filter_elem, 'test_action', '', ['', 'test_action'])

        filter_elem = Filter(parent_name='test_parent', action='test_action')
        self.compare_init(filter_elem, 'test_action', 'test_parent', ['test_parent', 'test_action'])

        filter_elem = Filter(ancestry=['a', 'b'], action="test")
        self.compare_init(filter_elem, 'test', '', ['a', 'b', 'test'])

        args = {'arg1': 'a', 'arg2': 3, 'arg3': u'abc'}
        expected_args_json = {'arg1': {'key': 'arg1', 'value': 'a', 'format': 'str'},
                              'arg2': {'key': 'arg2', 'value': '3', 'format': 'int'}}

        if sys.version_info < (3, 0):
            expected_args_json['arg3'] = {'key': 'arg3', 'value': 'abc', 'format': 'unicode'}
        else:
            expected_args_json['arg3'] = {'key': 'arg3', 'value': 'abc', 'format': 'str'}

        filter_elem = Filter(ancestry=['a', 'b'], action="test", args=args)
        self.compare_init(filter_elem, 'test', '', ['a', 'b', 'test'], args=expected_args_json)

    def test_as_json(self):
        filter_elem = Filter()
        self.assertDictEqual(filter_elem.as_json(), {'action': '', 'args': {}})

        filter_elem = Filter(action='test_action')
        self.assertDictEqual(filter_elem.as_json(), {'action': 'test_action', 'args': {}})

        args = {'arg1': 'a', 'arg2': 3, 'arg3': u'abc'}
        expected_args_json = {'arg1': {'key': 'arg1', 'value': 'a', 'format': 'str'},
                              'arg2': {'key': 'arg2', 'value': '3', 'format': 'int'}}
        if sys.version_info < (3, 0):
            expected_args_json['arg3'] = {'key': 'arg3', 'value': 'abc', 'format': 'unicode'}
        else:
            expected_args_json['arg3'] = {'key': 'arg3', 'value': 'abc', 'format': 'str'}

        expected_filter_json = {'action': 'test', 'args': expected_args_json}
        filter_elem = Filter(ancestry=['a', 'b'], action="test", args=args)
        self.assertDictEqual(filter_elem.as_json(), expected_filter_json)

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

    def test_validate_args(self):
        filter_elem = Filter()
        self.assertTrue(filter_elem.validate_args())

        filter_elem = Filter(action='length')
        self.assertTrue(filter_elem.validate_args())

        filter_elem = Filter(action='junkName')
        self.assertTrue(filter_elem.validate_args())

        self.test_funcs = {'filters': {'func_name1': {'args': []},
                                       'func_name2': {'args': [{'name': 'arg_name1', 'type': 'str'}]},
                                       'func_name3': {'args': [{'name': 'arg_name1', 'type': 'str'},
                                                               {'name': 'arg_name2', 'type': 'int'}]}}}
        corresponding_args = {'func_name1': {},
                              'func_name2': {'arg_name1': 'test_string'},
                              'func_name3': {'arg_name1': 'test_string', 'arg_name2': 6}}
        actions = ['func_name1', 'func_name2', 'func_name3', 'invalid_name']
        for action in actions:
            for arg_action, args in corresponding_args.items():
                filter_elem = Filter(action=action, args=args)
                if not args:
                    self.assertTrue(filter_elem.validate_args())

                elif action == 'invalid_name':
                    self.assertFalse(filter_elem.validate_args())
                elif action == arg_action:
                    if len(list(args.keys())) == len(list(self.test_funcs['filters'][action]['args'])):
                        self.assertTrue(filter_elem.validate_args())
                    else:
                        self.assertFalse(filter_elem.validate_args())
                else:
                    self.assertFalse(filter_elem.validate_args())

    def test_invalid_filter(self):
        filter_elem = Filter(action='junkAction')
        self.assertIsNone(filter_elem())
        self.assertEqual(filter_elem(output=6), 6)

    def test_length_filter(self):
        filter_elem = Filter(action='length')
        self.assertIsNone(filter_elem())
        self.assertEqual(filter_elem(output=6), 6)
        self.assertEqual(filter_elem(output=5.5), None)
        self.assertEqual(filter_elem(output=[3, 4, 5]), 3)
        self.assertEqual(filter_elem(output='aaab'), 4)
