import unittest

import yaml

from core.config.paths import walkoff_schema_path
from core.helpers import import_all_flags, import_all_filters
from core.validator import *
from tests.config import basic_app_api


class TestFlagFilterValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.filters = import_all_filters('tests.util.flagsfilters')
        cls.flags = import_all_flags('tests.util.flagsfilters')

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
        validate_flagfilter_params(self.basicapi[action_type],
                                   action_type,
                                   getattr(self, action_type),
                                   self.dereferencer)

    def __invalidate(self, action_type):
        self.__generate_resolver_dereferencer(self.basicapi)
        with self.assertRaises(InvalidApi):
            validate_flagfilter_params(self.basicapi[action_type],
                                       action_type,
                                       getattr(self, action_type),
                                       self.dereferencer)

    def test_flags_valid_run(self):
        self.basicapi['flags'] = {'flag1': {'run': 'mod1.flag1',
                                            'dataIn': 'value',
                                            'parameters': [{'name': 'value', 'required': True, 'type': 'string'}]}}
        self.__validate('flags')

    def test_filter_valid_run(self):
        self.basicapi['filters'] = {'filter1': {'run': 'mod1.filter1',
                                                'dataIn': 'value',
                                                'parameters': [{'name': 'value', 'required': True, 'type': 'string'}]}}
        self.__validate('filters')

    def test_flags_invalid_run(self):
        self.basicapi['flags'] = {'flag1': {'run': 'mod1.invalid',
                                            'dataIn': 'value',
                                            'parameters': [{'name': 'value', 'required': True, 'type': 'string'}]}}
        self.__invalidate('flags')

    def test_filters_invalid_run(self):
        self.basicapi['filters'] = {'filter1': {'run': 'mod1.invalid',
                                                'dataIn': 'value',
                                                'parameters': [{'name': 'value', 'required': True, 'type': 'string'}]}}
        self.__invalidate('filters')

    def test_flags_valid_datain_param(self):
        self.basicapi['flags'] = {'flag1': {'run': 'mod1.flag2',
                                            'dataIn': 'value',
                                            'parameters': [{'name': 'value', 'required': True, 'type': 'string'},
                                                           {'name': 'arg1', 'required': True, 'type': 'string'}]}}
        self.__validate('flags')

    def test_filters_valid_datain_param(self):
        self.basicapi['filters'] = {'filter1': {'run': 'mod1.filter2',
                                                'dataIn': 'value',
                                                'parameters': [{'name': 'value', 'required': True, 'type': 'string'},
                                                               {'name': 'arg1', 'type': 'string'}]}}
        self.__validate('filters')

    def test_flags_invalid_datain_param(self):
        self.basicapi['flags'] = {'flag1': {'run': 'mod1.flag2',
                                            'dataIn': 'invalid',
                                            'parameters': [{'name': 'value', 'required': True, 'type': 'string'},
                                                           {'name': 'arg1', 'required': True, 'type': 'string'}]}}
        self.__invalidate('flags')

    def test_filters_invalid_datain_param(self):
        self.basicapi['filters'] = {'filter1': {'run': 'mod1.filter2',
                                                'dataIn': 'invalid',
                                                'parameters': [{'name': 'value', 'required': True, 'type': 'string'},
                                                               {'name': 'arg1', 'type': 'string'}]}}
        self.__invalidate('filters')

    def test_flags_invalid_datain_param_not_required(self):
        self.basicapi['flags'] = {'flag1': {'run': 'mod1.flag2',
                                            'dataIn': 'invalid',
                                            'parameters': [{'name': 'value', 'type': 'string'},
                                                           {'name': 'arg1', 'required': True, 'type': 'string'}]}}
        self.__invalidate('flags')

    def test_filters_invalid_datain_param_not_required(self):
        self.basicapi['filters'] = {'filter1': {'run': 'mod1.filter2',
                                                'dataIn': 'invalid',
                                                'parameters': [{'name': 'value', 'type': 'string'},
                                                               {'name': 'arg1', 'type': 'string'}]}}
        self.__invalidate('filters')

    def test_flags_invalid_duplicate_param_names(self):
        self.basicapi['flags'] = {'flag1': {'run': 'mod1.flag2',
                                            'dataIn': 'invalid',
                                            'parameters': [{'name': 'value', 'type': 'string'},
                                                           {'name': 'value', 'required': True, 'type': 'integer'}]}}
        self.__invalidate('flags')

    def test_filters_invalid_duplicate_param_names(self):
        self.basicapi['filters'] = {'filter1': {'run': 'mod1.filter2',
                                                'dataIn': 'invalid',
                                                'parameters': [{'name': 'value', 'type': 'string'},
                                                               {'name': 'value', 'type': 'number'}]}}
        self.__invalidate('filters')

    def test_flags_invalid_mismatched_signature(self):
        self.basicapi['flags'] = {'flag1': {'run': 'mod1.flag2',
                                            'dataIn': 'invalid',
                                            'parameters': [{'name': 'value', 'type': 'string'},
                                                           {'name': 'arg1', 'required': True, 'type': 'integer'},
                                                           {'name': 'arg2', 'type': 'integer'}]}}
        self.__invalidate('flags')

    def test_filters_invalid_mismatched_signature(self):
        self.basicapi['filters'] = {'filter1': {'run': 'mod1.filter2',
                                                'dataIn': 'invalid',
                                                'parameters': [{'name': 'value', 'type': 'string'},
                                                               {'name': 'value', 'type': 'number'},
                                                               {'name': 'arg2', 'type': 'integer'}]}}
        self.__invalidate('filters')

    def test_multiple_flags_valid(self):
        self.basicapi['flags'] = {'flag1': {'run': 'mod1.flag1',
                                            'dataIn': 'value',
                                            'parameters': [{'name': 'value', 'required': True, 'type': 'string'}]},
                                  'flag2': {'run': 'mod1.flag2',
                                            'dataIn': 'value',
                                            'parameters': [{'name': 'value', 'required': True, 'type': 'string'},
                                                           {'name': 'arg1', 'required': True, 'type': 'string'}]}}
        self.__validate('flags')

    def test_multiple_filters_valid(self):
        self.basicapi['filters'] = {'filter1': {'run': 'mod1.filter1',
                                                'dataIn': 'value',
                                                'parameters': [{'name': 'value', 'required': True, 'type': 'string'}]},
                                    'filter2': {'run': 'mod1.filter2',
                                                'dataIn': 'value',
                                                'parameters': [{'name': 'value', 'required': True, 'type': 'string'},
                                                               {'name': 'arg1', 'required': True, 'type': 'string'}]}}
        self.__validate('filters')

    def test_multiple_flags_invalid(self):
        self.basicapi['flags'] = {'flag1': {'run': 'mod1.flag1',
                                            'dataIn': 'value',
                                            'parameters': [{'name': 'value', 'required': True, 'type': 'string'}]},
                                  'flag2': {'run': 'mod1.flag2',
                                            'dataIn': 'value',
                                            'parameters': [{'name': 'value', 'type': 'string'},
                                                           {'name': 'arg1', 'required': True, 'type': 'string'}]}}
        self.__invalidate('flags')

    def test_multiple_filters_invalid(self):
        self.basicapi['filters'] = {'filter1': {'run': 'mod1.filter1',
                                                'dataIn': 'value',
                                                'parameters': [{'name': 'value', 'required': True, 'type': 'string'}]},
                                    'filter2': {'run': 'mod1.filter2',
                                                'dataIn': 'value',
                                                'parameters': [{'name': 'value', 'required': True, 'type': 'string'},
                                                               {'name': 'value', 'required': True, 'type': 'integer'}]}}
        self.__invalidate('filters')
