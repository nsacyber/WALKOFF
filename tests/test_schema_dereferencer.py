# import unittest
# from core.schemas.dereference import *
# from core.helpers import InvalidApi
#
#
# class TestSchemaDereferencer(unittest.TestCase):
#     def test_dereference_basic(self):
#         schema = {
#             'a': 4,
#             'b': {'c': 5, 'd': 6}
#         }
#         self.assertEqual(dereference('#/a', schema, set(), ''), 4)
#
#     def test_dereference_deep(self):
#         schema = {
#             'a': 4,
#             'b': {'c': 5, 'd': 6}
#         }
#         self.assertEqual(dereference('#/b/c', schema, set(), ''), 5)
#
#     def test_dereference_invalid_path(self):
#         schema = {
#             'a': 4,
#             'b': {'c': 5, 'd': 6}
#         }
#         with self.assertRaises(InvalidApi):
#             dereference('#/b/invalid', schema, set(), '')
#
#     def test_dereference_invalid_path_no_hash(self):
#         schema = {
#             'a': 4,
#             'b': {'c': 5, 'd': 6}
#         }
#         with self.assertRaises(InvalidApi):
#             dereference('/b/invalid', schema, set(), '')
#
#     def test_dereference_invalid_path_empty(self):
#         schema = {
#             'a': 4,
#             'b': {'c': 5, 'd': 6}
#         }
#         with self.assertRaises(InvalidApi):
#             dereference('', schema, set(), '')
#
#     def test_dereference_invalid_path_empty_with_has(self):
#         schema = {
#             'a': 4,
#             'b': {'c': 5, 'd': 6}
#         }
#         with self.assertRaises(InvalidApi):
#             dereference('#/', schema, set(), '')
#
#     def test_dereference_with_seen(self):
#         schema = {
#             'a': 4,
#             'b': {'c': 5, 'd': 6}
#         }
#         self.assertEqual(dereference('#/b/c', schema, {'#/a'}, ''), 5)
#
#     def test_dereference_with_already_seen(self):
#         schema = {
#             'a': 4,
#             'b': {'c': 5, 'd': 6}
#         }
#         with self.assertRaises(InvalidApi):
#             dereference('#/b/c', schema, {'#/a', '#/b/c'}, '')
    #
    # def test_flatten_to_primitive(self):
    #     schema = {
    #         'a': 4,
    #         'b': {'$ref': '#/a'}
    #     }
    #     flatten()
    #     self.assertEqual(flatten({'$ref': '#/a'}, schema), 4)
    #
    # def test_flatten_to_dict(self):
    #     spec = {
    #         'a': {'a1': 3, 'a2': 4},
    #         'b': {'$ref': '#/a'}
    #     }
    #     schema = {'$ref': '#/a'}
    #     self.assertDictEqual(flatten(schema, spec, ''), {'a1': 3, 'a2': 4})
    #
    # def test_flatten_to_dict_with_other_top_level_elements(self):
    #     spec = {
    #         'a': {'a1': 3, 'a2': 4},
    #         'b': {'c': {'$ref': '#/a'}, 'd': {'e': 6, 'f': 7}}
    #     }
    #     schema = {'c': {'$ref': '#/a'}, 'd': {'e': 6, 'f': 7}}
    #     self.assertDictEqual(flatten(schema, spec, ''), {'c': {'a1': 3, 'a2': 4}, 'd': {'e': 6, 'f': 7}})
    #
    # def test_flatten_to_dict_with_multiple_references(self):
    #     spec = {
    #         'a': {'a1': 3, 'a2': 4},
    #         'b': {'c': {'$ref': '#/a'}, 'd': {'e': 6, 'f': 7}}
    #     }
    #     schema = {'c': {'$ref': '#/a'}, 'd': {'e': 6, 'f': {'$ref': '#/a/a1'}}}
    #     self.assertDictEqual(flatten(schema, spec, ''), {'c': {'a1': 3, 'a2': 4}, 'd': {'e': 6, 'f': 3}})

    # def test_flatten_to_dict_with_self_sub_reference(self):
    #     spec = {
    #         'a': {'a1': 3, 'a2': 4},
    #         'b': {'c': {'$ref': '#/a'},
    #               'd': {'e': {'$ref': '#/b/c'}, 'f': 7}}
    #     }
    #     schema = {'c': {'$ref': '#/a'},
    #               'd': {'e': {'$ref': '#/b/c'}, 'f': {'$ref': '#/a/a1'}}}
    #     self.assertDictEqual(flatten(schema, spec, '', ['b']), {'c': {'a1': 3, 'a2': 4}, 'd': {'e': 6, 'f': 3}})

    # def test_flatten_with_circular_reference(self):
    #     spec = {
    #         'a': {'a1': 3, 'a2': 4},
    #         'b': 5,
    #         'c': {'$ref': '#/d'},
    #         'd': {'$ref': '#/c'}
    #     }
    #     schema = {'$ref': '#/c'}
    #     with self.assertRaises(InvalidApi):
    #         flatten(schema, spec, '')
    #
    # def test_flatten_no_refs(self):
    #     spec = {
    #         'a': {'a1': 3, 'a2': 4},
    #         'b': 6
    #     }
    #     schema = {'a1': 3, 'a2': 4}
    #     self.assertDictEqual(flatten(schema, spec, ''), {'a1': 3, 'a2': 4})
    #
    # def test_flatten_primitive_array(self):
    #     spec = {
    #         'a': [1, 2, 3, 4],
    #         'b': 6
    #     }
    #     schema = [2, 3, 4, 5]
    #     self.assertListEqual(flatten(schema, spec, ''), [2, 3, 4, 5])
    #
    # def test_flatten_ref_to_primitive_array(self):
    #     spec = {
    #         'a': [1, 2, 3, 4],
    #         'b': 6
    #     }
    #     schema = {'$ref': '#/a'}
    #     self.assertListEqual(flatten(schema, spec, ''), [1, 2, 3, 4])
    #
    # def test_flatten_ref_to_object_array(self):
    #     spec = {
    #         'a': [{'c': 3, 'd': 5}, {'c': 6, 'd': 'e'}],
    #         'b': 6
    #     }
    #     schema = {'$ref': '#/a'}
    #     self.assertListEqual(flatten(schema, spec, ''), [{'c': 3, 'd': 5}, {'c': 6, 'd': 'e'}])
    #
    # def test_flatten_ref_to_object_array_with_ref(self):
    #     spec = {
    #         'a': [{'c': 3, 'd': 5}, {'c': 6, 'd': {'$ref': '#/b'}}],
    #         'b': 6
    #     }
    #     schema = {'$ref': '#/a'}
    #     self.assertListEqual(flatten(schema, spec, ''), [{'c': 3, 'd': 5}, {'c': 6, 'd': 6}])

    # def test_flatten_spec_sample_action(self):
    #     spec = {
    #         'actions': {
    #             'Json Sample': {'run': 'json_sample', 'description': 'Example',
    #                             'parameters': [
    #                                 {'name': 'json_in', 'required': True,
    #                                  'schema': {'$ref': '#/definitions/JsonSample'}},
    #                                 {'name': '$ref/definitions/Name1', 'required': True, 'type': 'string'}
    #                             ],
    #                             'returns': {'Success': {'description': 'success', 'schema': {'type': {'number'}}}}}},
    #         'definitions': {
    #             'JsonSample': {'type': 'object', 'properties': {'a': {'type': 'number'}, 'b': {'type': 'number'}}},
    #             'Name1': 'name1'
    #         }
    #     }
    #     expected = {
    #         'actions': {
    #             'Json Sample': {'run': 'json_sample', 'description': 'Example',
    #                             'parameters': [
    #                                 {'name': 'json_in', 'required': True,
    #                                  'schema': {'type': 'object',
    #                                             'properties': {'a': {'type': 'number'}, 'b': {'type': 'number'}}}},
    #                                 {'name': 'name1', 'required': True, 'type': 'string'}
    #                             ],
    #                             'returns': {'Success': {'description': 'success', 'schema': {'type': {'number'}}}}}},
    #         'definitions': {
    #             'JsonSample': {'type': 'object', 'properties': {'a': {'type': 'number'}, 'b': {'type': 'number'}}},
    #             'Name1': 'name1'
    #         }
    #     }
    #     self.assertDictEqual(flatten_spec(spec, ''), expected)