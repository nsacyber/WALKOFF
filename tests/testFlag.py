import unittest
import sys

from core.flag import Flag
from core.filter import Filter
from core.arguments import Argument


class TestFlag(unittest.TestCase):
    def compare_init(self, flag, action, parent_name, ancestry, filters, args):
        self.assertEqual(flag.action, action)
        self.assertEqual(flag.parent_name, parent_name)
        self.assertListEqual(flag.ancestry, ancestry)
        self.assertListEqual(flag.filters, filters)
        self.assertDictEqual({arg_name: arg_value.as_json() for arg_name, arg_value in flag.args.items()}, args)

    def test_init(self):
        flag = Flag()
        self.compare_init(flag, '', '', ['', ''], [], {})

        flag = Flag(parent_name='test_parent')
        self.compare_init(flag, '', 'test_parent', ['test_parent', ''], [], {})

        flag = Flag(action='test_action')
        self.compare_init(flag, 'test_action', '', ['', 'test_action'], [], {})

        flag = Flag(parent_name='test_parent', action='test_action', ancestry=['a', 'b'])
        self.compare_init(flag, 'test_action', 'test_parent', ['a', 'b', 'test_action'], [], {})

        filters = [Filter(action='test_filter_action'), Filter()]
        flag = Flag(action='test_action', filters=filters)
        self.compare_init(flag, 'test_action', '', ['', 'test_action'], filters, {})

        args = {'arg1': 'a', 'arg2': 3, 'arg3': u'abc'}
        args = {arg_name: Argument(key=arg_name, value=arg_value, format=type(arg_value).__name__)
                for arg_name, arg_value in args.items()}
        expected_arg_json = {arg_name: arg_value.as_json() for arg_name, arg_value in args.items()}
        flag = Flag(action='test_action', args=args)
        self.compare_init(flag, 'test_action', '', ['', 'test_action'], [], expected_arg_json)

        flag = Flag(parent_name='test_parent', action='test_action', ancestry=['a', 'b'], filters=filters, args=args)
        self.compare_init(flag, 'test_action', 'test_parent', ['a', 'b', 'test_action'], filters, expected_arg_json)

    def test_set(self):
        filters = [Filter(action='test_filter_action'), Filter()]
        args = {'arg1': 'a', 'arg2': 3, 'arg3': u'abc'}
        args = {arg_name: Argument(key=arg_name, value=arg_value, format=type(arg_value).__name__)
                for arg_name, arg_value in args.items()}
        flag = Flag(parent_name='test_parent', action='test_action', ancestry=['a', 'b'], filters=filters, args=args)
        flag.set('action', 'renamed_action')
        self.assertEqual(flag.action, 'renamed_action')
        flag.set('filters', [])
        self.assertListEqual(flag.filters, [])
        flag.set('args', {})
        self.assertDictEqual(flag.args, {})

    def test_set_non_existent(self):
        filters = [Filter(action='test_filter_action'), Filter()]
        args = {'arg1': 'a', 'arg2': 3, 'arg3': u'abc'}
        args = {arg_name: Argument(key=arg_name, value=arg_value, format=type(arg_value).__name__)
                for arg_name, arg_value in args.items()}
        flag = Flag(parent_name='test_parent', action='test_action', ancestry=['a', 'b'], filters=filters, args=args)

        flag.set('junkfield', 'junk')
        self.assertEqual(flag.junkfield, 'junk')

    def test_to_from_xml(self):
        filters = [Filter(action='test_filter_action'), Filter()]
        args = {'arg1': 'a', 'arg2': 3, 'arg3': u'abc'}
        args = {arg_name: Argument(key=arg_name, value=arg_value, format=type(arg_value).__name__)
                for arg_name, arg_value in args.items()}

        flags = [Flag(),
                 Flag(parent_name='test_parent'),
                 Flag(action='test_action'),
                 Flag(parent_name='test_parent', action='test_action', ancestry=['a', 'b']),
                 Flag(action='test_action', filters=filters),
                 Flag(action='test_action', args=args),
                 Flag(parent_name='test_parent', action='test_action', ancestry=['a', 'b'], filters=filters, args=args)]

        for flag in flags:
            original_flag = flag.as_json()
            derived_flag = Flag(xml=flag.to_xml()).as_json()
            self.assertDictEqual(derived_flag, original_flag)

    def test_add_filter(self):
        filters = [Filter(action='test_filter_action'), Filter()]
        filters_cpy = list(filters)
        flag = Flag(action='test_action', filters=filters)
        flag.add_filter()
        self.assertEqual(len(flag.filters), len(filters_cpy) + 1)
        self.assertDictEqual(flag.filters[-1].as_json(), Filter(action='', args={}).as_json())

        args = {'arg1': 'a', 'arg2': 3, 'arg3': u'abc'}
        flag.add_filter(action='test_add', args=args)
        self.assertEqual(len(flag.filters), len(filters_cpy) + 2)
        self.assertDictEqual(flag.filters[-1].as_json(), Filter(action='test_add', args=args).as_json())

        flag.add_filter(action='test_add2', index=0)
        self.assertEqual(len(flag.filters), len(filters_cpy) + 3)
        self.assertDictEqual(flag.filters[0].as_json(), Filter(action='test_add2', args={}).as_json())

        flag.add_filter(action='test_add3', index=len(filters_cpy) + 3)
        self.assertEqual(len(flag.filters), len(filters_cpy) + 4)
        self.assertDictEqual(flag.filters[-1].as_json(), Filter(action='test_add3', args={}).as_json())

        flag.add_filter(action='test_add4', index=1000)
        self.assertEqual(len(flag.filters), len(filters_cpy) + 5)
        self.assertDictEqual(flag.filters[-1].as_json(), Filter(action='test_add4', args={}).as_json())

        flag.add_filter(action='test_add5', index=-1)
        self.assertEqual(len(flag.filters), len(filters_cpy) + 6)
        self.assertDictEqual(flag.filters[-2].as_json(), Filter(action='test_add5', args={}).as_json())

        flag.add_filter(action='test_add6', index=-100)
        self.assertEqual(len(flag.filters), len(filters_cpy) + 7)
        self.assertDictEqual(flag.filters[0].as_json(), Filter(action='test_add6', args={}).as_json())

    def test_delete_filter(self):
        filters = [Filter(action='test_filter_action'),
                   Filter(),
                   Filter(action='a'),
                   Filter(action='b'),
                   Filter(action='c')]
        flag = Flag(action='test_action', filters=filters)
        self.assertTrue(flag.remove_filter())
        self.assertEqual(len(flag.filters), 4)
        self.assertDictEqual(flag.filters[-1].as_json(), Filter(action='b').as_json())

        self.assertTrue(flag.remove_filter(1))
        self.assertEqual(len(flag.filters), 3)
        self.assertDictEqual(flag.filters[1].as_json(), Filter(action='a').as_json())

        self.assertTrue(flag.remove_filter(-2))
        self.assertEqual(len(flag.filters), 2)
        self.assertDictEqual(flag.filters[-2].as_json(), Filter(action='test_filter_action').as_json())

        self.assertFalse(flag.remove_filter(1000))
        self.assertEqual(len(flag.filters), 2)
        self.assertFalse(flag.remove_filter(-1000))
        self.assertEqual(len(flag.filters), 2)

        self.assertTrue(flag.remove_filter(0))
        self.assertEqual(len(flag.filters), 1)
        self.assertDictEqual(flag.filters[-1].as_json(), Filter(action='b').as_json())

        self.assertTrue(flag.remove_filter(-1))
        self.assertEqual(len(flag.filters), 0)
        self.assertListEqual(flag.filters, [])

        self.assertFalse(flag.remove_filter())
        self.assertListEqual(flag.filters, [])

    def test_validate_args(self):
        # TODO: Complete this test!!!!!
        pass

    def test_as_json(self):
        filters = [Filter(action='test_filter_action'), Filter()]
        args = {'arg1': 'a', 'arg2': 3, 'arg3': u'abc'}
        args = {arg_name: Argument(key=arg_name, value=arg_value, format=type(arg_value).__name__)
                for arg_name, arg_value in args.items()}
        args_json = {'arg2': {'format': 'int', 'key': 'arg2', 'value': '3'},
                     'arg1': {'format': 'str', 'key': 'arg1', 'value': 'a'}}

        if sys.version_info < (3, 0):
            args_json['arg3'] = {'key': 'arg3', 'value': 'abc', 'format': 'unicode'}
        else:
            args_json['arg3'] = {'key': 'arg3', 'value': 'abc', 'format': 'str'}

        input_output = {Flag(): {'args': {}, 'action': '', 'filters': []},
                        Flag(parent_name='test_parent'): {'args': {}, 'action': '', 'filters': []},
                        Flag(action='test_action'): {'args': {}, 'action': 'test_action', 'filters': []},
                        Flag(parent_name='test_parent', action='test_action', ancestry=['a', 'b']):
                            {'args': {}, 'action': 'test_action', 'filters': []},
                        Flag(action='test_action', filters=filters):
                            {'args': {},
                             'action': 'test_action',
                             'filters': [{'args': {}, 'action': 'test_filter_action'}, {'args': {}, 'action': ''}]},
                        Flag(action='test_action', args=args): {'args': args_json,
                                                                'action': 'test_action', 'filters': []},
                        Flag(parent_name='test_parent', action='test_action', ancestry=['a', 'b'], filters=filters,
                             args=args): {'args': args_json,
                                          'action': 'test_action',
                                          'filters': [{'args': {}, 'action': 'test_filter_action'},
                                                      {'args': {}, 'action': ''}]}
                        }
        for input, expected in input_output.items():
            self.assertDictEqual(input.as_json(), expected)

    def test_from_json(self):
        filters = [Filter(action='test_filter_action'), Filter()]
        args = {'arg1': 'a', 'arg2': 3, 'arg3': u'abc'}
        args = {arg_name: Argument(key=arg_name, value=arg_value, format=type(arg_value).__name__)
                for arg_name, arg_value in args.items()}
        input_output = {Flag(): ('', ['']),
                        Flag(parent_name='test_parent'): ('test_parent', ['test_parent']),
                        Flag(action='test_action'): ('', ['']),
                        Flag(parent_name='test_parent', action='test_action', ancestry=['a', 'b']): ('test_parent', ['a', 'b']),

                        Flag(action='test_action', args=args): ('', [''])}

        flag1, expected1 = Flag(action='test_action'), ('', [''])
        filters1 = [Filter(parent_name=flag1.name, ancestry=flag1.ancestry),
                    Filter(action='test_filter_action', parent_name=flag1.name, ancestry=flag1.ancestry)]
        flag1.filters = filters1

        flag2, expected2 = Flag(parent_name='test_parent', action='test_action', ancestry=['a', 'b'], filters=filters,
                                args=args), ('test_parent', ['a', 'b'])
        filters2 = [Filter(parent_name=flag2.name, ancestry=flag2.ancestry),
                    Filter(action='test_filter_action', parent_name=flag2.name, ancestry=flag2.ancestry)]
        flag2.filters = filters2

        input_output[flag1] = expected1
        input_output[flag2] = expected2

        for flag, (parent_name, ancestry) in input_output.items():
            flag_json = flag.as_json()
            original_filter_ancestries = [list(filter_element.ancestry) for filter_element in flag.filters]
            derived_flag = Flag.from_json(flag_json, parent_name=parent_name, ancestry=ancestry)
            derived_filters_ancestries = [list(filter_element.ancestry) for filter_element in derived_flag.filters]
            self.assertEqual(len(derived_filters_ancestries), len(original_filter_ancestries))
            for derived_filter_ancestry, original_filter_ancestry in zip(derived_filters_ancestries,
                                                                         original_filter_ancestries):
                self.assertListEqual(derived_filter_ancestry, original_filter_ancestry)
            self.assertDictEqual(derived_flag.as_json(), flag_json)
            self.assertEqual(flag.parent_name, derived_flag.parent_name)
            self.assertListEqual(flag.ancestry, derived_flag.ancestry)

