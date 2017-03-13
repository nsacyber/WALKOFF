import unittest
from core.step import Step
from core.nextstep import Next
from apps.HelloWorld.main import Main
from core.helpers import load_function_aliases


class TestStep(unittest.TestCase):
    def test_function_alias_lookup_same_function(self):
        existing_actions = ['helloWorld', 'repeatBackToMe', 'returnPlusOne']
        app = 'HelloWorld'
        for action in existing_actions:
            step = Step(action=action, app=app)
            self.assertEqual(step._Step__lookup_function(), action)

    def test_function_alias_lookup(self):
        app = 'HelloWorld'
        function_aliases = load_function_aliases(app)
        self.assertIsNotNone(function_aliases)
        for function, aliases in function_aliases.items():
            for alias in aliases:
                step = Step(action=alias, app=app)
                self.assertEqual(step._Step__lookup_function(), function)

    def test_function_alias_lookup_invalid(self):
        app = 'HelloWorld'
        step = Step(action='JunkAction1', app=app)
        self.assertEqual(step._Step__lookup_function(), 'JunkAction1')

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
            step.conditionals = [Next(name=name, parent_name=step.name, ancestry=list(step.ancestry))
                                 for name in input_params['next']]
            step.errors = [Next(name=name, parent_name=step.name, ancestry=list(step.ancestry))
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
