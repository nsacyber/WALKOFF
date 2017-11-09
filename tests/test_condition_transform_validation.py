import unittest

import yaml

from core.config.paths import walkoff_schema_path
import core.config.config
from core.validator import *
from tests.config import basic_app_api, test_apps_path
import apps


class TestConditionTransformValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apps.clear_cache()
        apps.cache_apps(test_apps_path)
        core.config.config.load_app_apis(test_apps_path)
        cls.conditions = apps.get_all_conditions_for_app('HelloWorld')
        cls.transforms = apps.get_all_transforms_for_app('HelloWorld')

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()

    def setUp(self):
        with open(basic_app_api, 'r') as f:
            self.basicapi = yaml.load(f.read())

    def __generate_resolver_dereferencer(self, spec, expected_success=True):
        try:
            walkoff_resolver = validate_spec_json(spec, walkoff_schema_path, '', None)
        except Exception as e:
            if expected_success:
                self.fail('Unexpectedly invalid app api. Error: {}'.format(e))
            else:
                raise
        self.dereferencer = partial(deref, resolver=walkoff_resolver)

    def __validate(self, action_type):
        self.__generate_resolver_dereferencer(self.basicapi)
        validate_condition_transform_params(self.basicapi[action_type],
                                            'HelloWorld',
                                            action_type.title()[:-1],
                                            getattr(self, action_type),
                                            self.dereferencer)

    def __invalidate(self, action_type):
        self.__generate_resolver_dereferencer(self.basicapi)
        with self.assertRaises(InvalidApi):
            validate_condition_transform_params(self.basicapi[action_type],
                                                'HelloWorld',
                                                action_type.title()[:-1],
                                                getattr(self, action_type),
                                                self.dereferencer)

    def test_conditions_valid_run(self):
        self.basicapi['conditions'] = {'flag1': {'run': 'conditions.flag1',
                                                 'data_in': 'value',
                                                 'parameters': [{'name': 'value', 'required': True, 'type': 'string'}]}}
        self.__validate('conditions')

    def test_transform_valid_run(self):
        self.basicapi['transforms'] = {'filter1': {'run': 'transforms.top_level_filter',
                                                   'data_in': 'value',
                                                   'parameters': [
                                                       {'name': 'value', 'required': True, 'type': 'number'}],
                                                   'returns': {'Success': {'schema': {'type': 'object'}}}}}
        self.__validate('transforms')

    def test_conditions_invalid_run(self):
        self.basicapi['conditions'] = {'flag1': {'run': 'conditions.invalid',
                                                 'data_in': 'value',
                                                 'parameters': [{'name': 'value', 'required': True, 'type': 'string'}]}}
        self.__invalidate('conditions')

    def test_transforms_invalid_run(self):
        self.basicapi['transforms'] = {'filter1': {'run': 'transforms.invalid',
                                                   'data_in': 'value',
                                                   'parameters': [
                                                       {'name': 'value', 'required': True, 'type': 'string'}],
                                                   'returns': {'Success': {'schema': {'type': 'object'}}}}}
        self.__invalidate('transforms')

    def test_conditions_valid_datain_param(self):
        self.basicapi['conditions'] = {'flag1': {'run': 'conditions.flag2',
                                                 'data_in': 'value',
                                                 'parameters': [{'name': 'value', 'required': True, 'type': 'string'},
                                                                {'name': 'arg1', 'required': True, 'type': 'string'}]}}
        self.__validate('conditions')

    def test_transforms_valid_datain_param(self):
        self.basicapi['transforms'] = {'filter1': {'run': 'transforms.filter2',
                                                   'data_in': 'value',
                                                   'parameters': [{'name': 'value', 'required': True, 'type': 'string'},
                                                                  {'name': 'arg1', 'type': 'string'}],
                                                   'returns': {'Success': {'schema': {'type': 'object'}}}}}
        self.__validate('transforms')

    def test_conditions_invalid_datain_param(self):
        self.basicapi['conditions'] = {'flag1': {'run': 'conditions.flag2',
                                                 'data_in': 'invalid',
                                                 'parameters': [{'name': 'value', 'required': True, 'type': 'string'},
                                                                {'name': 'arg1', 'required': True, 'type': 'string'}]}}
        self.__invalidate('conditions')

    def test_transforms_invalid_datain_param(self):
        self.basicapi['transforms'] = {'filter1': {'run': 'transforms.filter2',
                                                   'data_in': 'invalid',
                                                   'parameters': [{'name': 'value', 'required': True, 'type': 'string'},
                                                                  {'name': 'arg1', 'type': 'string'}],
                                                   'returns': {'Success': {'schema': {'type': 'object'}}}}}
        self.__invalidate('transforms')

    def test_conditions_invalid_datain_param_not_required(self):
        self.basicapi['conditions'] = {'flag1': {'run': 'conditions.flag2',
                                                 'data_in': 'invalid',
                                                 'parameters': [{'name': 'value', 'type': 'string'},
                                                                {'name': 'arg1', 'required': True, 'type': 'string'}]}}
        self.__invalidate('conditions')

    def test_transforms_invalid_datain_param_not_required(self):
        self.basicapi['transforms'] = {'filter1': {'run': 'transforms.filter2',
                                                   'data_in': 'invalid',
                                                   'parameters': [{'name': 'value', 'type': 'string'},
                                                                  {'name': 'arg1', 'type': 'string'}],
                                                   'returns': {'Success': {'schema': {'type': 'object'}}}}}
        self.__invalidate('transforms')

    def test_conditions_invalid_duplicate_param_names(self):
        self.basicapi['conditions'] = {'flag1': {'run': 'conditions.flag2',
                                                 'data_in': 'invalid',
                                                 'parameters': [{'name': 'value', 'type': 'string'},
                                                                {'name': 'value', 'required': True,
                                                                 'type': 'integer'}]}}
        self.__invalidate('conditions')

    def test_transforms_invalid_duplicate_param_names(self):
        self.basicapi['transforms'] = {'filter1': {'run': 'transforms.filter2',
                                                   'data_in': 'invalid',
                                                   'parameters': [{'name': 'value', 'type': 'string'},
                                                                  {'name': 'value', 'type': 'number'}],
                                                   'returns': {'Success': {'schema': {'type': 'object'}}}}}
        self.__invalidate('transforms')

    def test_conditions_invalid_mismatched_signature(self):
        self.basicapi['conditions'] = {'flag1': {'run': 'conditions.flag2',
                                                 'data_in': 'invalid',
                                                 'parameters': [{'name': 'value', 'type': 'string'},
                                                                {'name': 'arg1', 'required': True, 'type': 'integer'},
                                                                {'name': 'arg2', 'type': 'integer'}]}}
        self.__invalidate('conditions')

    def test_transforms_invalid_mismatched_signature(self):
        self.basicapi['transforms'] = {'filter1': {'run': 'transforms.filter2',
                                                   'data_in': 'invalid',
                                                   'parameters': [{'name': 'value', 'type': 'string'},
                                                                  {'name': 'value', 'type': 'number'},
                                                                  {'name': 'arg2', 'type': 'integer'}],
                                                   'returns': {'Success': {'schema': {'type': 'object'}}}}}
        self.__invalidate('transforms')

    def test_multiple_conditions_valid(self):
        self.basicapi['conditions'] = {'flag1': {'run': 'conditions.flag1',
                                                 'data_in': 'value',
                                                 'parameters': [{'name': 'value', 'required': True, 'type': 'string'}]},
                                       'flag2': {'run': 'conditions.flag2',
                                                 'data_in': 'value',
                                                 'parameters': [{'name': 'value', 'required': True, 'type': 'string'},
                                                                {'name': 'arg1', 'required': True, 'type': 'string'}]}}
        self.__validate('conditions')

    def test_multiple_transforms_valid(self):
        self.basicapi['transforms'] = {'filter1': {'run': 'transforms.top_level_filter',
                                                   'data_in': 'value',
                                                   'parameters': [
                                                       {'name': 'value', 'required': True, 'type': 'number'}],
                                                   'returns': {'Success': {'schema': {'type': 'object'}}}},
                                       'filter2': {'run': 'transforms.filter2',
                                                   'data_in': 'value',
                                                   'parameters': [{'name': 'value', 'required': True, 'type': 'string'},
                                                                  {'name': 'arg1', 'required': True,
                                                                   'type': 'string'}],
                                                   'returns': {'Success': {'schema': {'type': 'object'}}}}}
        self.__validate('transforms')

    def test_multiple_conditions_invalid(self):
        self.basicapi['conditions'] = {'flag1': {'run': 'conditions.flag1',
                                                 'data_in': 'value',
                                                 'parameters': [{'name': 'value', 'required': True, 'type': 'string'}]},
                                       'flag2': {'run': 'conditions.flag2',
                                                 'data_in': 'value',
                                                 'parameters': [{'name': 'value', 'type': 'string'},
                                                                {'name': 'arg1', 'required': True, 'type': 'string'}]}}
        self.__invalidate('conditions')

    def test_multiple_transforms_invalid(self):
        self.basicapi['transforms'] = {'filter1': {'run': 'transforms.filter1',
                                                   'data_in': 'value',
                                                   'parameters': [
                                                       {'name': 'value', 'required': True, 'type': 'string'}],
                                                   'returns': {'Success': {'schema': {'type': 'object'}}}},
                                       'filter2': {'run': 'transforms.filter2',
                                                   'data_in': 'value',
                                                   'parameters': [{'name': 'value', 'required': True, 'type': 'string'},
                                                                  {'name': 'value', 'required': True,
                                                                   'type': 'integer'}],
                                                   'returns': {'Success': {'schema': {'type': 'object'}}}}}
        self.__invalidate('transforms')
