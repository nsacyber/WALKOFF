import unittest
import copy

from core.arguments import Argument
from core.flag import Flag
from core.step import Step, InvalidStepActionError
from core.nextstep import NextStep
import core.config.config
import core.config.paths
from tests.util.assertwrappers import assert_raises_with_error
from tests.config import test_apps_path


class TestStep(unittest.TestCase):
    def setUp(self):
        core.config.paths.apps_path = test_apps_path
        core.config.config.load_function_info()
        self.original_functions = copy.deepcopy(core.config.config.function_info)
        self.test_funcs = {'func_name1': {'args': []},
                           'func_name2': {'args': [{'name': 'arg_name1', 'type': 'arg_type1'}]},
                           'func_name3': {'args': [{'name': 'arg_name1', 'type': 'arg_type1'},
                                                   {'name': 'arg_name2', 'type': 'arg_type2'}]}}
        apps = ['app1', 'app2', 'app3']

        for app in apps:
            core.config.config.function_info['apps'][app] = copy.deepcopy(self.test_funcs)

    def tearDown(self):
        core.config.config.function_info = self.original_functions

    def __compare_init(self, elem, name, parent_name, action, app, device, inputs, next_steps, errors, ancestry):
        self.assertEqual(elem.name, name)
        self.assertEqual(elem.parent_name, parent_name)
        self.assertEqual(elem.action, action)
        self.assertEqual(elem.app, app)
        self.assertEqual(elem.device, device)
        self.assertDictEqual({key: input_element.as_json() for key, input_element in elem.input.items()}, inputs)
        self.assertListEqual([conditional.as_json() for conditional in elem.conditionals], next_steps)
        self.assertListEqual([error.as_json() for error in elem.errors], errors)
        self.assertListEqual(elem.ancestry, ancestry)
        self.assertIsNone(elem.output)

    def test_init(self):
        step = Step()
        self.__compare_init(step, '', '', '', '', '', {}, [], [], ['', ''])

        step = Step(name='name')
        self.__compare_init(step, 'name', '', '', '', '', {}, [], [], ['', 'name'])

        step = Step(name='name', parent_name='parent_name')
        self.__compare_init(step, 'name', 'parent_name', '', '', '', {}, [], [], ['parent_name', 'name'])

        step = Step(name='name', parent_name='parent_name', action='action')
        self.__compare_init(step, 'name', 'parent_name', 'action', '', '', {}, [], [], ['parent_name', 'name'])

        step = Step(name='name', parent_name='parent_name', action='action')
        self.__compare_init(step, 'name', 'parent_name', 'action', '', '', {}, [], [], ['parent_name', 'name'])

        step = Step(name='name', parent_name='parent_name', action='action', app='app')
        self.__compare_init(step, 'name', 'parent_name', 'action', 'app', '', {}, [], [], ['parent_name', 'name'])

        step = Step(name='name', parent_name='parent_name', action='action', app='app', device='device')
        self.__compare_init(step, 'name', 'parent_name', 'action', 'app', 'device',
                            {}, [], [], ['parent_name', 'name'])

        inputs = {'in1': 'a', 'in2': 3, 'in3': u'abc'}
        inputs = {arg_name: Argument(key=arg_name, value=arg_value, format=type(arg_value).__name__)
                  for arg_name, arg_value in inputs.items()}

        step = Step(name='name', parent_name='parent_name', action='action', app='app', device='device', inputs=inputs)
        self.__compare_init(step, 'name', 'parent_name', 'action', 'app', 'device',
                            {key: input_.as_json() for key, input_ in inputs.items()}, [], [], ['parent_name', 'name'])

        flags = [Flag(), Flag(action='action')]
        nexts = [NextStep(),
                 NextStep(name='name'),
                 NextStep(name='name', parent_name='parent', flags=flags, ancestry=['a', 'b'])]
        step = Step(name='name', parent_name='parent_name', action='action', app='app', device='device',
                    inputs=inputs, next_steps=nexts)
        self.__compare_init(step, 'name', 'parent_name', 'action', 'app', 'device',
                            {key: input_.as_json() for key, input_ in inputs.items()},
                            [next_.as_json() for next_ in nexts],
                            [], ['parent_name', 'name'])

        error_flags = [Flag(), Flag(action='action'), Flag()]
        errors = [NextStep(),
                  NextStep(name='name'),
                  NextStep(name='name', parent_name='parent', flags=error_flags, ancestry=['a', 'b'])]
        step = Step(name='name', parent_name='parent_name', action='action', app='app', device='device',
                    inputs=inputs, next_steps=nexts, errors=errors)
        self.__compare_init(step, 'name', 'parent_name', 'action', 'app', 'device',
                            {key: input_.as_json() for key, input_ in inputs.items()},
                            [next_.as_json() for next_ in nexts],
                            [error.as_json() for error in errors], ['parent_name', 'name'])

    def test_function_alias_lookup_same_function(self):
        existing_actions = ['helloWorld', 'repeatBackToMe', 'returnPlusOne']
        app = 'HelloWorld'
        for action in existing_actions:
            step = Step(action=action, app=app)
            self.assertEqual(step._Step__lookup_function(), action)

    def test_function_alias_lookup(self):
        app = 'HelloWorld'
        function_aliases = {action: info['aliases']
                            for action, info in core.config.config.function_info['apps']['HelloWorld'].items()}
        self.assertIsNotNone(function_aliases)
        for function, aliases in function_aliases.items():
            for alias in aliases:
                step = Step(action=alias, app=app)
                self.assertEqual(step._Step__lookup_function(), function)

    def test_function_alias_lookup_invalid(self):
        app = 'HelloWorld'
        step = Step(action='JunkAction1', app=app)
        assert_raises_with_error(self,
                                 InvalidStepActionError,
                                 'Error: Step action JunkAction1 not found for app HelloWorld',
                                 step._Step__lookup_function)

    def test_validate_input(self):
        apps = ['app1', 'app2', 'app3', 'invalid_app']
        actions = ['func_name1', 'func_name2', 'func_name3', 'invalid_action']

        for app in apps:
            for action in actions:
                for arg_action, args in self.test_funcs.items():
                    test_args = {arg['name']: Argument(key=arg['name'], format=arg['type'])
                                 for arg in args['args']}
                    step = Step(app=app, action=action, inputs=test_args)
                    if app == 'invalid_app' or action == 'invalid_action':
                        self.assertFalse(step.validate_input())
                    elif action == arg_action or not self.test_funcs[action]['args']:
                        self.assertTrue(step.validate_input())
                    else:
                        self.assertFalse(step.validate_input())

    def test_from_json(self):
        next_step_names = ['next1', 'next2']
        error_names = ['error1', 'error2']
        inputs = [{'name': 'name1',
                   'action': 'action1',
                   'app': 'app1',
                   'device': 'dev1',
                   'next': [],
                   'error': []},

                  {'name': 'name2',
                   'action': 'action2',
                   'app': 'app2',
                   'device': 'opt2',
                   'next': next_step_names,
                   'error': []},

                  {'name': 'name3',
                   'action': 'action3',
                   'app': 'app3',
                   'device': 'opt3',
                   'next': [],
                   'error': error_names},

                  {'name': 'name4',
                   'action': 'action4',
                   'app': 'app4',
                   'device': 'dev4',
                   'next': next_step_names,
                   'error': error_names}]
        for input_params in inputs:
            step = Step(name=input_params['name'],
                        action=input_params['action'],
                        app=input_params['app'],
                        device=input_params['device'])
            step.conditionals = [NextStep(name=name, parent_name=step.name, ancestry=list(step.ancestry))
                                 for name in input_params['next']]
            step.errors = [NextStep(name=name, parent_name=step.name, ancestry=list(step.ancestry))
                           for name in input_params['error']]
            step_json = step.as_json()
            derived_step = Step.from_json(step_json, parent_name=step.parent_name, ancestry=list(step.ancestry)[:-1])
            self.assertDictEqual(derived_step.as_json(), step_json)
            self.assertEqual(step.parent_name, derived_step.parent_name)
            self.assertListEqual(step.ancestry, derived_step.ancestry)

            # check the ancestry of the next_steps
            original_next_step_ancestries = [list(next_step.ancestry) for next_step in step.conditionals]
            derived_next_step_ancestries = [list(next_step.ancestry) for next_step in derived_step.conditionals]
            self.assertEqual(len(original_next_step_ancestries), len(derived_next_step_ancestries))
            for original_next_step_ancestry, derived_next_step_ancestry in zip(original_next_step_ancestries,
                                                                               derived_next_step_ancestries):
                self.assertListEqual(derived_next_step_ancestry, original_next_step_ancestry)

            # check the ancestry of the next_steps
            original_error_ancestries = [list(error.ancestry) for error in step.errors]
            derived_error_ancestries = [list(error.ancestry) for error in derived_step.errors]
            self.assertEqual(len(original_error_ancestries), len(derived_error_ancestries))
            for original_error_ancestry, derived_error_ancestry in zip(original_error_ancestries,
                                                                       derived_error_ancestries):
                self.assertListEqual(derived_error_ancestry, original_error_ancestry)
