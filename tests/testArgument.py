import unittest
import copy
from xml.etree import ElementTree

from core.arguments import Argument
from core import config


class TestArgument(unittest.TestCase):
    def setUp(self):
        self.original_functions = copy.deepcopy(config.functionConfig)
        self.test_funcs = {'func_name1': {'args': []},
                           'func_name2': {'args': [{'name': 'arg_name1', 'type': 'arg_type1'}]},
                           'func_name3': {'args': [{'name': 'arg_name1', 'type': 'arg_type1'},
                                                   {'name': 'arg_name2', 'type': 'arg_type2'}]}}
        for func_name, arg_dict in self.test_funcs.items():
            config.functionConfig[func_name] = arg_dict

    def tearDown(self):
        config.functionConfig = self.original_functions

    def test_init(self):
        arg = Argument()
        self.assertIsNone(arg.key)
        self.assertEqual(arg.format, 'str')
        self.assertIsNone(arg.templated)
        self.assertEqual(arg.value, 'None')

        arg = Argument(key='test')
        self.assertEqual(arg.key, 'test')
        self.assertEqual(arg.format, 'str')
        self.assertIsNone(arg.templated)
        self.assertEqual(arg.value, 'None')

        arg = Argument(key='test', value='val')
        self.assertEqual(arg.key, 'test')
        self.assertEqual(arg.format, 'str')
        self.assertIsNone(arg.templated)
        self.assertEqual(arg.value, 'val')

        arg = Argument(key='test', format='int')
        self.assertEqual(arg.key, 'test')
        self.assertEqual(arg.format, 'int')
        self.assertIsNone(arg.templated)
        self.assertEqual(arg.value, None)

        arg = Argument(key='test', format='int', value='6')
        self.assertEqual(arg.key, 'test')
        self.assertEqual(arg.format, 'int')
        self.assertIsNone(arg.templated)
        self.assertEqual(arg.value, 6)

    def test_to_from_json(self):
        input_output = {Argument(): {'key': 'None', 'value': 'None', 'format': 'str'},
                        Argument(key='test'): {'key': 'test', 'value': 'None', 'format': 'str'},
                        Argument(key='test', value='val'): {'key': 'test', 'value': 'val', 'format': 'str'},
                        Argument(key='test', format='int'): {'key': 'test', 'value': 'None', 'format': 'int'},
                        Argument(key='test', format='int', value='6'): {'key': 'test', 'value': '6', 'format': 'int'}}
        for arg, expected_json in input_output.items():
            original_json = arg.as_json()
            self.assertDictEqual(original_json, expected_json)
            self.assertDictEqual(Argument.from_json(original_json).as_json(), expected_json)

        arg = Argument(key='test', format='int', value='6')
        arg2 = Argument.from_json(arg.as_json())
        self.assertEqual(arg2.value, 6)

    def test_convert_to_string(self):
        self.assertEqual(Argument.convertTo(), 'None')
        string_types = ['str', 'string', 'unicode']
        string_converted_attempts = (6, 'a', None, 4.56, {6: "this_string"}, ['a', 'b'])
        for string_type in string_types:
            self.assertEqual(Argument.convertTo(type=string_type), 'None')
        for string_type in string_types:
            for attempt in string_converted_attempts:
                self.assertEqual(Argument.convertTo(value=attempt, type=string_type), str(attempt))

    def test_convert_to_int(self):
        self.assertIsNone(Argument.convertTo(type='int'))
        int_convert_attempts = ((6, 6), (4.5, 4), ('6', 6), ('4.5', '4.5'))
        for int_type, expected in int_convert_attempts:
            self.assertEqual(Argument.convertTo(value=int_type, type='int'), expected)

    def test_convert_to_unspecified_type(self):
        unknown_types = ['list', 'dict', 'float', 'tuple', 'set', 'junk']
        attempts = (6, 'a', None, 4.56, {6: "this_string"}, ['a', 'b'])
        for input_type in unknown_types:
            for attempt in attempts:
                self.assertEqual(Argument.convertTo(value=attempt, type=input_type), attempt)

    def test_template(self):
        def test_help(template_expected, key, value, format):
            arg = Argument(key=key, value=value, format=format)
            self.assertEqual(arg.template(), template_expected)
            self.assertEqual(arg.templated, template_expected)

        test_cases = (('None', None, None, 'str'),
                      ('None', 'test', None, 'str'),
                      ('val', 'test', 'val', 'str'),
                      ('None', 'test', None, 'int'),
                      ('6', 'test', '6', 'int'))
        for case in test_cases:
            test_help(*case)

    def test_call(self):
        def test_help(template_expected, key, value, format, expected_value):
            arg = Argument(key=key, value=value, format=format)
            self.assertEqual(arg(), expected_value)
            self.assertEqual(arg.template(), template_expected)
            self.assertEqual(arg(), template_expected)

        test_cases = (('None', None, None, 'str', 'None'),
                      ('None', 'test', None, 'str', 'None'),
                      ('val', 'test', 'val', 'str', 'val'),
                      ('None', 'test', None, 'int', None),
                      ('6', 'test', '6', 'int', 6))
        for case in test_cases:
            test_help(*case)

    def test_validate(self):
        for action, args in self.test_funcs.items():
            for arg_pair in args['args']:
                arg = Argument(key=arg_pair['name'], format=arg_pair['type'])
                self.assertTrue(arg.validate(action=action))

        test_funcs = {'func_name2': {'args': []},
                      'func_name3': {'args': [{'name': 'junk_name1', 'type': 'junk_type1'},
                                              {'name': 'junk_name2', 'type': 'junk_type2'}]}}
        for action, args in test_funcs.items():
            for arg_pair in args['args']:
                arg = Argument(key=arg_pair['name'], format=arg_pair['type'])
                self.assertFalse(arg.validate(action=action))

    def test_to_xml(self):
        arg = Argument()
        xml = arg.to_xml()
        self.assertIsNone(xml)

        input_args = [Argument(key='test'),
                      Argument(key='test', value='val'),
                      Argument(key='test', format='int'),
                      Argument(key='test', format='int', value='6')]

        for arg in input_args:
            arg_xml = arg.to_xml()
            derived_arg = Argument(key=arg_xml.tag, value=arg_xml.text, format=arg_xml.get("format"))
            self.assertDictEqual(derived_arg.as_json(), arg.as_json())
