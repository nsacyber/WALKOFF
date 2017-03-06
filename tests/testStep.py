import unittest
from core.step import Step
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
        self.assertIsNone(step._Step__lookup_function(), 'JunkAction1')




