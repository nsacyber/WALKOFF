from unittest import TestCase

from walkoff.core.argument import Argument
from walkoff.core.helpers import InvalidArgument


class TestArgument(TestCase):
    def assert_init_equals(self, arg, name, value=None, reference=None, selection=None):
        self.assertEqual(arg.name, name)
        if value is None:
            self.assertIsNone(arg.value)
        else:
            self.assertEqual(arg.value, value)

        if reference is None:
            self.assertIsNone(arg.reference)
        else:
            self.assertEqual(arg.reference, reference)

        if selection is None:
            self.assertIsNone(arg.selection)
        else:
            self.assertListEqual(arg.selection, selection)

    def test_init_no_value_or_reference(self):
        with self.assertRaises(InvalidArgument):
            Argument('test')

    def test_init_no_value_empty_reference(self):
        with self.assertRaises(InvalidArgument):
            Argument('test', reference='')

    def test_init_with_value(self):
        arg = Argument('test_name', value=5)
        self.assert_init_equals(arg, 'test_name', value=5)

    def test_init_with_reference(self):
        arg = Argument('test_name', reference='some_uid')
        self.assert_init_equals(arg, 'test_name', reference='some_uid')

    def test_init_with_reference_empty(self):
        arg = Argument('test_name', value=5, reference='')
        self.assert_init_equals(arg, 'test_name', value=5)

    def test_init_with_selection_empty(self):
        arg = Argument('test_name', value=5, selection=[])
        self.assert_init_equals(arg, 'test_name', value=5)

    def test_init_with_selection(self):
        arg = Argument('test_name', reference='some_uid', selection=[1, 'a', 2])
        self.assert_init_equals(arg, 'test_name', reference='some_uid', selection=[1, 'a', 2])

    def test_get_next_selection_key_on_dict(self):
        self.assertEqual(Argument._get_next_selection({'a': 1, '2': 'something'}, 'a'), 1)

    def test_get_next_selection_key_on_list(self):
        with self.assertRaises(ValueError):
            Argument._get_next_selection(['a', 1, '2', 'something'], 'a')

    def test_get_next_selection_key_on_value(self):
        with self.assertRaises(ValueError):
            Argument._get_next_selection('something', 'a')

    def test_get_next_selection_index_on_dict(self):
        with self.assertRaises(KeyError):
            Argument._get_next_selection({'a': 1, '2': 'something'}, 3)

    def test_get_next_selection_int_index_on_list(self):
        self.assertEqual(Argument._get_next_selection(['a', 1, '2', 'something'], 3), 'something')

    def test_get_next_selection_str_index_on_list(self):
        self.assertEqual(Argument._get_next_selection(['a', 1, '2', 'something'], '3'), 'something')

    def test_get_next_selection_index_on_list_out_of_bounds(self):
        with self.assertRaises(IndexError):
            Argument._get_next_selection(['a', 1, '2', 'something'], 10)

    def test_select_one_on_list(self):
        arg = Argument('test', reference='some_uid', selection=[1])
        self.assertEqual(arg._select(['a', 'b', 'c']), 'b')

    def test_select_one_on_list_out_of_range(self):
        arg = Argument('test', reference='some_uid', selection=[10])
        with self.assertRaises(InvalidArgument):
            arg._select(['a', 'b', 'c'])

    def test_select_one_on_dict(self):
        arg = Argument('test', reference='some_uid', selection=['b'])
        self.assertEqual(arg._select({'a': 1, 'b': 2, 'c': 3}), 2)

    def test_select_one_on_dict_key_error(self):
        arg = Argument('test', reference='some_uid', selection=['d'])
        with self.assertRaises(InvalidArgument):
            arg._select({'a': 1, 'b': 2, 'c': 3})

    def test_select_one_on_value(self):
        arg = Argument('test', reference='some_uid', selection=['d'])
        with self.assertRaises(InvalidArgument):
            arg._select('some raw value')

    def test_select(self):
        arg = Argument('test', reference='some_uid', selection=['a', 0, '1', 'b'])
        input_ = {'a': [[{'one': 1},
                         {'three': 3, 'b': 4}],
                        [{'one': 1}, {'two': 2}]],
                  'b': 15,
                  'c': 'something'}
        self.assertEqual(arg._select(input_), 4)

    def test_select_selection_too_deep(self):
        arg = Argument('test', reference='some_uid', selection=['a', 0, '1', 'b', 10])
        input_ = {'a': [[{'one': 1},
                         {'three': 3, 'b': 4}],
                        [{'one': 1}, {'two': 2}]],
                  'b': 15,
                  'c': 'something'}
        with self.assertRaises(InvalidArgument):
            arg._select(input_)

    def test_get_action_from_reference_empty_accumulator(self):
        arg = Argument('test', reference='a')
        with self.assertRaises(InvalidArgument):
            arg._get_action_from_reference({})

    def test_get_action_from_reference_not_in_accumulator(self):
        arg = Argument('test', reference='a')
        with self.assertRaises(InvalidArgument):
            arg._get_action_from_reference({'b': 3, 'c': 7})

    def test_get_action_from_reference(self):
        arg = Argument('test', reference='a')
        self.assertEqual(arg._get_action_from_reference({'a': 1, 'b': 3, 'c': 7}), 1)

    def test_get_value_value_only(self):
        arg = Argument('test', value=42)
        self.assertEqual(arg.get_value({}), 42)

    def test_get_value_value_with_reference(self):
        arg = Argument('test', value=42, reference='a')
        self.assertEqual(arg.get_value({'a': 1}), 42)

    def test_get_value_reference_only(self):
        arg = Argument('test', reference='a')
        self.assertEqual(arg.get_value({'a': 1, 'b': 2}), 1)

    def test_get_value_reference_not_found(self):
        arg = Argument('test', reference='c')
        with self.assertRaises(InvalidArgument):
            arg.get_value({'a': 1, 'b': 2})

    def test_get_value_reference_and_selection(self):
        arg = Argument('test', reference='a', selection=['a', 0, '1', 'b'])
        input_ = {'a': [[{'one': 1},
                         {'three': 3, 'b': 4}],
                        [{'one': 1}, {'two': 2}]],
                  'b': 15,
                  'c': 'something'}
        self.assertEqual(arg.get_value({'a': input_, 'b': 2}), 4)

    def test_get_value_reference_and_bad_selection(self):
        arg = Argument('test', reference='a', selection=['a', 0, '1', 'invalid'])
        input_ = {'a': [[{'one': 1},
                         {'three': 3, 'b': 4}],
                        [{'one': 1}, {'two': 2}]],
                  'b': 15,
                  'c': 'something'}
        with self.assertRaises(InvalidArgument):
            arg.get_value({'a': input_, 'b': 2})
