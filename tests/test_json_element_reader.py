from unittest import TestCase

from walkoff.core.executionelements.executionelement import ExecutionElement
from walkoff.core.jsonelementreader import JsonElementReader


class A(ExecutionElement):
    def __init__(self, c):
        self.c = c


class B(ExecutionElement):
    def __init__(self, d):
        self.d = d


class TestJsonElementReader(TestCase):
    def test_single_primitive_value_not_execution_element(self):
        class Test(object):
            def __init__(self):
                self.a = 42

        test = Test()
        self.assertDictEqual(JsonElementReader.read(test), {'a': 42})

    def test_single_primitive_value_execution_element(self):
        class Test(ExecutionElement):
            def __init__(self):
                self.b = 'something'

        test = Test()
        self.assertDictEqual(JsonElementReader.read(test), {'b': 'something'})

    def test_single_primitive_value_execution_element_with_function(self):
        class Test(ExecutionElement):
            def __init__(self):
                self.b = 'something'

            def x(self): pass

        test = Test()
        self.assertDictEqual(JsonElementReader.read(test), {'b': 'something'})

    def test_single_primitive_value_execution_element_with_protected_field(self):
        class Test(ExecutionElement):
            def __init__(self):
                self.b = 'something'
                self._c = 'shouldn\'t be there'

        test = Test()
        self.assertDictEqual(JsonElementReader.read(test), {'b': 'something'})

    def test_single_primitive_value_execution_element_with_private_field(self):
        class Test(ExecutionElement):
            def __init__(self):
                self.b = 'something'
                self.__c = 'shouldn\'t be there'

        test = Test()
        self.assertDictEqual(JsonElementReader.read(test), {'b': 'something'})

    def test_multiple_primitive_values_not_execution_element(self):
        class Test(object):
            def __init__(self):
                self.a = 42
                self.b = True

        test = Test()
        self.assertDictEqual(JsonElementReader.read(test), {'a': 42, 'b': True})

    def test_multiple_primitive_values_execution_element(self):
        class Test(ExecutionElement):
            def __init__(self):
                self.a = 42
                self.b = True

        test = Test()
        self.assertDictEqual(JsonElementReader.read(test), {'a': 42, 'b': True})

    def test_not_execution_element_with_list_all_primitives(self):
        class Test(object):
            def __init__(self):
                self.a = 42
                self.b = ['a', 'True', True]

        test = Test()
        self.assertDictWithListEqual(JsonElementReader.read(test), {'a': 42, 'b': ['a', 'True', True]}, 'b')

    def test_execution_element_with_list_all_primitives(self):
        class Test(ExecutionElement):
            def __init__(self):
                self.a = 42
                self.b = [True, 'b', 17]

        test = Test()
        self.assertDictWithListEqual(JsonElementReader.read(test), {'a': 42, 'b': [True, 'b', 17]}, 'b')

    def assertDictWithListEqual(self, dict_, expected, list_key):
        actual_list = dict_.pop(list_key, None)
        self.assertIsNotNone(actual_list)
        expected_list = expected.pop(list_key, None)
        self.assertIsNotNone(expected_list)
        self.assertDictEqual(dict_, expected)
        for list_element in actual_list:
            self.assertIn(list_element, expected_list)

    def test_not_execution_element_with_list_all_execution_elements(self):
        class Test(object):
            def __init__(self):
                self.a = 42
                self.b = [A('a'), A('True'), A(True)]

        test = Test()
        self.assertDictWithListEqual(JsonElementReader.read(test),
                                     {'a': 42, 'b': [{'c': 'a'}, {'c': 'True'}, {'c': True}]}, 'b')

    def test_execution_element_with_list_all_execution_elements(self):
        class Test(ExecutionElement):
            def __init__(self):
                self.a = 42
                self.b = [A(True), A('b'), A(17)]

        test = Test()
        self.assertDictWithListEqual(JsonElementReader.read(test), {'a': 42, 'b': [{'c': True}, {'c': 'b'}, {'c': 17}]},
                                     'b')

    def test_not_execution_element_with_list_some_execution_elements(self):
        class Test(object):
            def __init__(self):
                self.a = 42
                self.b = [A('a'), 'True', A(True)]

        test = Test()
        self.assertDictWithListEqual(JsonElementReader.read(test), {'a': 42, 'b': [{'c': 'a'}, 'True', {'c': True}]},
                                     'b')

    def test_execution_element_with_list_some_execution_elements(self):
        class Test(ExecutionElement):
            def __init__(self):
                self.a = 42
                self.b = [A(True), 'b', 17]

        test = Test()
        self.assertDictWithListEqual(JsonElementReader.read(test), {'a': 42, 'b': [{'c': True}, 'b', 17]}, 'b')

    def test_not_execution_element_with_dict_all_primitives(self):
        class Test(object):
            def __init__(self):
                self.a = 42
                self.b = {'a': 'True', 'c': True}

        test = Test()
        self.assertDictWithListEqual(JsonElementReader.read(test),
                                     {'a': 42, 'b': [{'name': 'a', 'value': 'True'}, {'name': 'c', 'value': True}]},
                                     'b')

    def test_execution_element_with_dict_all_primitives(self):
        class Test(ExecutionElement):
            def __init__(self):
                self.a = 42
                self.b = {True: 'b', 'd': 17}

        test = Test()
        self.assertDictWithListEqual(JsonElementReader.read(test),
                                     {'a': 42, 'b': [{'name': True, 'value': 'b'}, {'name': 'd', 'value': 17}]}, 'b')

    def test_not_execution_element_with_dict_all_execution_elements(self):
        class Test(object):
            def __init__(self):
                self.a = 42
                self.b = {'a': A('True'), 'c': A(True)}

        test = Test()
        self.assertDictWithListEqual(JsonElementReader.read(test),
                                     {'a': 42, 'b': [{'c': 'True'}, {'c': True}]}, 'b')

    def test_execution_element_with_dict_all_execution_elements(self):
        class Test(ExecutionElement):
            def __init__(self):
                self.a = 42
                self.b = {True: A('b'), 'd': A(17)}

        test = Test()
        self.assertDictWithListEqual(JsonElementReader.read(test),
                                     {'a': 42, 'b': [{'c': 'b'}, {'c': 17}]}, 'b')

    def test_not_execution_element_with_dict_some_execution_elements(self):
        class Test(object):
            def __init__(self):
                self.a = 42
                self.b = {'a': 'True', 'c': True, 'd': A('42')}

        test = Test()
        self.assertDictWithListEqual(JsonElementReader.read(test),
                                     {'a': 42, 'b': [{'name': 'a', 'value': 'True'}, {'name': 'c', 'value': True}]},
                                     'b')

    def test_execution_element_with_dict_some_execution_elements(self):
        class Test(ExecutionElement):
            def __init__(self):
                self.a = 42
                self.b = {True: 'b', 'd': 17, 'b': A(37)}

        test = Test()
        self.assertDictWithListEqual(JsonElementReader.read(test),
                                     {'a': 42, 'b': [{'name': True, 'value': 'b'}, {'name': 'd', 'value': 17}]}, 'b')

    def test_nested_in_dict(self):
        class Test(ExecutionElement):
            def __init__(self):
                self.a = 42
                self.b = {True: A(B('b')), 'd': A(B(17)), 'b': A(B(37))}

        test = Test()
        self.assertDictWithListEqual(JsonElementReader.read(test), {'a': 42, 'b': [{'c': {'d': 'b'}},
                                                                                   {'c': {'d': 37}},
                                                                                   {'c': {'d': 17}}]}, 'b')

    def test_nested_in_list(self):
        class A2(ExecutionElement):
            def __init__(self, b):
                self.a = 'static'
                self.b = [A(b + i) for i in range(3)]

        class Test(ExecutionElement):
            def __init__(self):
                self.a = 42
                self.b = [A2(1), A2(2), A2(3)]

        test = Test()
        self.assertDictWithListEqual(JsonElementReader.read(test),
                                     {'a': 42,
                                      'b': [{'a': 'static', 'b': [{'c': 1}, {'c': 2}, {'c': 3}]},
                                            {'a': 'static', 'b': [{'c': 2}, {'c': 3}, {'c': 4}]},
                                            {'a': 'static', 'b': [{'c': 3}, {'c': 4}, {'c': 5}]}]}, 'b')
