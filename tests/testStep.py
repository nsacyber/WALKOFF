import unittest
import copy

from core.arguments import Argument
from core.flag import Flag
from core.step import Step, InvalidStepActionError, InvalidStepInputError
from core.nextstep import NextStep
import core.config.config
import core.config.paths
from tests.util.assertwrappers import assert_raises_with_error
from tests.config import test_apps_path
from core.instance import Instance

from server import flaskserver as server


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

    def test_to_from_xml(self):
        inputs = {'in1': 'a', 'in2': 3, 'in3': u'abc'}
        inputs = {arg_name: Argument(key=arg_name, value=arg_value, format=type(arg_value).__name__)
                  for arg_name, arg_value in inputs.items()}
        flags = [Flag(), Flag(action='action')]
        next_steps = [NextStep(),
                      NextStep(name='name'),
                      NextStep(name='name', parent_name='parent', flags=flags, ancestry=['a', 'b'])]
        error_flags = [Flag(), Flag(action='action'), Flag()]
        errors = [NextStep(),
                  NextStep(name='name'),
                  NextStep(name='name', parent_name='parent', flags=error_flags, ancestry=['a', 'b'])]
        steps = [Step(),
                 Step(name='name'),
                 Step(name='name', parent_name='parent_name'),
                 Step(name='name', parent_name='parent_name', action='action'),
                 Step(name='name', parent_name='parent_name', action='action', app='app'),
                 Step(name='name', parent_name='parent_name', action='action', app='app', device='device'),
                 Step(name='name', parent_name='parent_name', action='action', app='app', device='device',
                      inputs=inputs),
                 Step(name='name', parent_name='parent_name', action='action', app='app', device='device',
                      inputs=inputs, next_steps=next_steps),
                 Step(name='name', parent_name='parent_name', action='action', app='app', device='device',
                      inputs=inputs, next_steps=next_steps, errors=errors),
                 Step(name='name', parent_name='parent_name', action='action', app='app', device='device',
                      inputs=inputs, next_steps=next_steps, errors=errors, position={'x': 5, 'y': -40.3})]
        for step in steps:
            original_json = step.as_json()
            new_step = Step(xml=step.to_xml())
            new_json = new_step.as_json()
            self.assertDictEqual(new_json, original_json)

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
        action = 'JunkAction1'
        step = Step(action=action, app=app)
        assert_raises_with_error(self,
                                 InvalidStepActionError,
                                 'Error: Step action {0} not found for app {1}'.format(action, app),
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

    def test_execute(self):
        app = 'HelloWorld'
        with server.running_context.flask_app.app_context():
            instance = Instance.create(app_name=app, device_name='test_device_name')
        actions = [('helloWorld', {}, {"message": "HELLO WORLD"}),
                   ('repeatBackToMe', {'call': Argument(key='call', value='HelloWorld', format='str')},
                    "REPEATING: HelloWorld"),
                   ('returnPlusOne', {'number': Argument(key='number', value='6', format='str')}, '7')]

        for action, inputs, output in actions:
            step = Step(app=app, action=action, inputs=inputs)
            self.assertEqual(step.execute(instance=instance()), output)
            self.assertEqual(step.output, output)

    def test_execute_invalid_inputs(self):
        app = 'HelloWorld'
        actions = [('invalid_name', {'call': Argument(key='call', value='HelloWorld', format='str')}),
                   ('repeatBackToMe', {'number': Argument(key='number', value='6', format='str')}),
                   ('returnPlusOne', {})]

        for action, inputs in actions:
            step = Step(app=app, action=action, inputs=inputs)
            with server.running_context.flask_app.app_context():
                instance = Instance.create(app_name=app, device_name='test_device_name')
            with self.assertRaises(InvalidStepInputError):
                step.execute(instance=instance())

    def test_get_next_step(self):
        flags1 = [Flag(action='regMatch', args={'regex': Argument(key='regex', value='(.*)', format='str')})]
        flags2 = [Flag(action='regMatch', args={'regex': Argument(key='regex', value='(.*)', format='str')}),
                  Flag(action='regMatch', args={'regex': Argument(key='regex', value='a', format='str')})]

        next_step1 = NextStep(name='name1', flags=[])
        next_step2 = NextStep(name='name2', flags=flags1)
        next_step3 = NextStep(name='name3', flags=flags2)

        step1 = Step(next_steps=[next_step1])
        self.assertEqual(step1.get_next_step(), next_step1.name)
        self.assertEqual(step1.next_up, next_step1.name)
        step1.output = 'aaaa'
        self.assertEqual(step1.get_next_step(), next_step1.name)
        self.assertEqual(step1.next_up, next_step1.name)

        step2 = Step(next_steps=[next_step2])
        step2.output = 'aaaa'
        self.assertEqual(step2.get_next_step(), next_step2.name)
        self.assertEqual(step2.next_up, next_step2.name)

        step3 = Step(next_steps=[next_step3])
        step3.output = 'aaaa'
        self.assertEqual(step3.get_next_step(), next_step3.name)
        self.assertEqual(step3.next_up, next_step3.name)
        step3.output = None
        self.assertIsNone(step3.get_next_step())
        self.assertEqual(step3.next_up, next_step3.name)

        step4 = Step(next_steps=[next_step1, next_step2])
        step4.output = 'aaaa'
        self.assertEqual(step4.get_next_step(), next_step1.name)
        self.assertEqual(step4.next_up, next_step1.name)
        step4.output = None
        self.assertEqual(step4.get_next_step(), next_step1.name)
        self.assertEqual(step4.next_up, next_step1.name)

        step4 = Step(next_steps=[next_step2, next_step1])
        step4.output = 6
        self.assertEqual(step4.get_next_step(), next_step2.name)
        self.assertEqual(step4.next_up, next_step2.name)

        step5 = Step(next_steps=[next_step3, next_step2])
        step5.output = 6
        self.assertEqual(step5.get_next_step(), next_step2.name)
        self.assertEqual(step5.next_up, next_step2.name)
        step5.output = 'aaa'
        self.assertEqual(step5.get_next_step(), next_step3.name)
        self.assertEqual(step5.next_up, next_step3.name)

    def test_get_next_step_with_errors(self):
        flags1 = [Flag(action='regMatch', args={'regex': Argument(key='regex', value='(.*)', format='str')})]
        flags2 = [Flag(action='regMatch', args={'regex': Argument(key='regex', value='(.*)', format='str')}),
                  Flag(action='regMatch', args={'regex': Argument(key='regex', value='a', format='str')})]

        next_step1 = NextStep(name='name1', flags=flags1)
        next_step2 = NextStep(name='name2', flags=flags2)

        step1 = Step(next_steps=[next_step2, next_step1], errors=[])
        step1.output = 'aaaa'
        self.assertEqual(step1.get_next_step(), next_step2.name)
        self.assertEqual(step1.next_up, next_step2.name)
        step1.output = 'aaa'
        self.assertIsNone(step1.get_next_step(error=True))
        self.assertEqual(step1.next_up, next_step2.name)

        step2 = Step(next_steps=[next_step1], errors=[next_step2])
        step2.output = 'bbbb'
        self.assertEqual(step2.get_next_step(), next_step1.name)
        step2.output = 'aaa'
        self.assertEqual(step2.get_next_step(error=True), next_step2.name)
        self.assertEqual(step2.next_up, next_step2.name)

        step3 = Step(next_steps=[], errors=[next_step2, next_step1])
        self.assertIsNone(step3.get_next_step())
        step3.output = 'bbbbb'
        self.assertEqual(step3.get_next_step(error=True), next_step1.name)
        self.assertEqual(step3.next_up, next_step1.name)
        step3.output = 'aaa'
        self.assertEqual(step3.get_next_step(error=True), next_step2.name)
        self.assertEqual(step3.next_up, next_step2.name)

    def test_to_from_json(self):
        next_step_names = ['next1', 'next2']
        error_names = ['error1', 'error2']
        inputs = [{'name': 'name1',
                   'action': 'action1',
                   'app': 'app1',
                   'device': 'dev1',
                   'next': [],
                   'error': [],
                   'position': {}},

                  {'name': 'name2',
                   'action': 'action2',
                   'app': 'app2',
                   'device': 'opt2',
                   'next': next_step_names,
                   'error': [],
                   'position': {'x': 3, 'y': 5}},

                  {'name': 'name3',
                   'action': 'action3',
                   'app': 'app3',
                   'device': 'opt3',
                   'next': [],
                   'error': error_names,
                   'position': {'x': 30, 'y': -5}},

                  {'name': 'name4',
                   'action': 'action4',
                   'app': 'app4',
                   'device': 'dev4',
                   'next': next_step_names,
                   'error': error_names,
                  'position': {'x': 40.237, 'y': -100}}]
        for input_params in inputs:
            step = Step(name=input_params['name'],
                        action=input_params['action'],
                        app=input_params['app'],
                        device=input_params['device'],
                        position=input_params['position'])
            step.conditionals = [NextStep(name=name, parent_name=step.name, ancestry=list(step.ancestry))
                                 for name in input_params['next']]
            step.errors = [NextStep(name=name, parent_name=step.name, ancestry=list(step.ancestry))
                           for name in input_params['error']]
            step_json = step.as_json()
            derived_step = Step.from_json(step_json,
                                          step_json['position'],
                                          parent_name=step.parent_name,
                                          ancestry=list(step.ancestry)[:-1])
            self.assertDictEqual(derived_step.as_json(), step_json)
            self.assertEqual(step.parent_name, derived_step.parent_name)
            self.assertListEqual(step.ancestry, derived_step.ancestry)

            derived_step_without_children = step_json
            derived_step_without_children['next'] = [next_step['name']
                                                     for next_step in derived_step_without_children['next']]
            derived_step_without_children['errors'] = [error['name']
                                                       for error in derived_step_without_children['errors']]
            self.assertDictEqual(derived_step.as_json(with_children=False), derived_step_without_children)

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

    def test_get_children(self):
        step = Step()
        names = ['step1', 'step2', 'step3']
        for name in names:
            self.assertIsNone(step.get_children([name]))
            self.assertDictEqual(step.get_children([]), step.as_json(with_children=False))

        next_steps = [NextStep(name='name1'), NextStep(name='name2'), NextStep(name='name3')]
        names = ['name1', 'name2', 'name3']
        step = Step(next_steps=next_steps)
        for i, name in enumerate(names):
            self.assertDictEqual(step.get_children([name]), next_steps[i].as_json())

        step = Step(errors=next_steps)
        for i, name in enumerate(names):
            self.assertDictEqual(step.get_children([name]), next_steps[i].as_json())

        errors = [NextStep(name='name1'), NextStep(name='error1'), NextStep(name='error2'), NextStep(name='name2')]
        next_names = list(names)
        error_names = ['error1', 'error2']
        all_names = list(next_names)
        all_names.extend(error_names)

        step = Step(next_steps=next_steps, errors=errors)

        for i, name in enumerate(all_names):
            if not name.startswith('error'):
                self.assertDictEqual(step.get_children([name]), next_steps[i].as_json())
            else:
                self.assertDictEqual(step.get_children([name]), errors[i-2].as_json())

        flags = [Flag(), Flag(action='action1'), Flag(action='action2')]
        next_steps = [NextStep(name='name1', flags=flags)]
        names = ['', 'action1', 'action2']
        step = Step(next_steps=next_steps)
        ancestries = [[name, 'name1'] for name in names]
        for i, ancestry in enumerate(ancestries):
            self.assertDictEqual(step.get_children(ancestry), flags[i].as_json())