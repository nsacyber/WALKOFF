from walkoff.executiondb.yamlconstructable import YamlChild, YamlConstructable
from unittest import TestCase


class TestYamlChild(TestCase):

    def test_expand(self):
        class Child(YamlConstructable):
            pass

        child = YamlChild('field', Child, expansion='child')
        yaml = {
            'field': {
                'name1': {'a': 1, 'b': 2, 'c': 'd'},
                'name2': {'a': 3, 'e': 'f'}
            }
        }
        expected = {
            'field': [
                {'child': 'name1', 'a': 1, 'b': 2, 'c': 'd'},
                {'child': 'name2', 'a': 3, 'e': 'f'}
            ]
        }
        child._expand(yaml)
        self.assertDictEqual(yaml, expected)

    def test_construct_child_no_field(self):
        class Child(YamlConstructable):
            counter = 0

            @classmethod
            def from_api_yaml(cls, yaml, *additional_keys):
                cls.counter += 1

        child = YamlChild('invalid', Child)
        yaml = {
            'field': {
                'name1': {'a': 1, 'b': 2, 'c': 'd'},
                'name2': {'a': 3, 'e': 'f'}
            }
        }
        expected = {
            'field': {
                'name1': {'a': 1, 'b': 2, 'c': 'd'},
                'name2': {'a': 3, 'e': 'f'}
            }
        }
        child.construct_child(yaml)
        self.assertDictEqual(yaml, expected)

    def test_construct_child(self):
        class Child(YamlConstructable):
            call_history = []

            @classmethod
            def from_api_yaml(cls, yaml, **additional_keys):
                cls.call_history.append((yaml, additional_keys))
                return yaml

        child = YamlChild('field', Child, expansion='child')
        yaml = {
            'field': {
                'name1': {'a': 1, 'b': 2, 'c': 'd'},
            }
        }
        expected_call = (
            [
                {'child': 'name1', 'a': 1, 'b': 2, 'c': 'd'},
            ],
            {}
        )
        expected_yaml = {
            'field': [
                {'child': 'name1', 'a': 1, 'b': 2, 'c': 'd'},
            ]
        }
        child.construct_child(yaml)
        self.assertEqual(len(Child.call_history), 1)
        self.assertDictEqual(Child.call_history[0][0][0], expected_call[0][0])
        self.assertDictEqual(Child.call_history[0][1], expected_call[1])
        self.assertDictEqual(yaml, expected_yaml)


class TestYamlConstructable(TestCase):

    def test_from_api_yaml_dict(self):
        yaml = {'a': 1, 'b': 2, 'c': 'd'}

        class A(YamlConstructable):
            def __init__(self, **args):
                self.init_args = args

        a = A.from_api_yaml(yaml)
        self.assertDictEqual(a.init_args, yaml)

    def test_from_api_yaml_with_custom_x_elements(self):
        yaml = {'a': 1, 'b': 2, 'c': 'd', 'x-custom1': 3, 'x-Custom2': 'def'}
        expected = {'a': 1, 'b': 2, 'c': 'd'}

        class A(YamlConstructable):
            def __init__(self, **args):
                self.init_args = args

        a = A.from_api_yaml(yaml)
        self.assertDictEqual(a.init_args, expected)

    def test_from_api_yaml_with_schema(self):
        yaml = {'a': 1, 'b': 2, 'c': 'd', 'e': 'abc', 'f': 23}

        expected = {'a': 1, 'b': 2, 'c': 'd', 'schema': {'e': 'abc', 'f': 23}}

        class A(YamlConstructable):
            a = 12
            b = None
            c = 'something'
            schema = {}

            def __init__(self, **args):
                self.init_args = args

        a = A.from_api_yaml(yaml)
        self.assertDictEqual(a.init_args, expected)

    def test_from_api_yaml_with_children(self):
        yaml = {
            'a': 23,
            'b': 'd',
            'c': [
                {'child': 'name1', 'a': 1, 'b': 2, 'c': 'd'},
                {'child': 'name2', 'a': 3, 'e': 'f'}
            ],
            'd': {
                'act1': {'3': 4, '2': 1},
            }
        }

        expected = {
            'a': 23,
            'b': 'd',
            'c': [
                {'child': 'name1', 'a': 1, 'b': 2, 'c': 'd'},
                {'child': 'name2', 'a': 3, 'e': 'f'}
            ],
            'd': [
                {'name': 'act1', '3': 4, '2': 1},
            ]
        }

        class MockChild(YamlConstructable):
            def __init__(self, **init_args):
                self.init_args = init_args

        class ChildC(MockChild):
            pass

        class ChildD(MockChild):
            pass

        class A(YamlConstructable):
            _children = (
                YamlChild('c', ChildC),
                YamlChild('d', ChildD, expansion='name')
            )

            def __init__(self, **args):
                self.init_args = args

        a = A.from_api_yaml(yaml)
        self.assertSetEqual(set(a.init_args.keys()), set(expected.keys()))
        self.assertEqual(a.init_args['a'], 23)
        self.assertEqual(a.init_args['b'], 'd')
        self.assertEqual(len(a.init_args['c']), 2)
        self.assertTrue(all(isinstance(c, ChildC) for c in a.init_args['c']))
        for i in range(2):
            self.assertEqual(a.init_args['c'][i].init_args, expected['c'][i])

        self.assertEqual(len(a.init_args['d']), 1)
        self.assertTrue(isinstance(a.init_args['d'][0], ChildD))
        self.assertEqual(a.init_args['d'][0].init_args, expected['d'][0])
