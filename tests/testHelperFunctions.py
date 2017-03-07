import unittest
from core.helpers import *

from core.instance import Instance
from tests.config import testWorkflowsPath


class TestHelperFunctions(unittest.TestCase):
    def test_load_function_aliases(self):
        aliases = load_function_aliases('HelloWorld')
        expected_aliases = {
            "helloWorld": ["helloworld", "hello world", "hello", "greeting", "HelloWorld", "hello_world"],
            "repeatBackToMe": ["parrot", "Parrot", "RepeatBackToMe", "repeat_back_to_me", "repeat"],
            "returnPlusOne": ["plus one", "PlusOne", "plus_one", "plusone", "++", "increment"]
        }
        self.assertDictEqual(aliases, expected_aliases)

    def test_load_function_aliases_invalid_app(self):
        self.assertIsNone(load_function_aliases('JunkAppName'))

    def test_load_app_function(self):

        app = 'HelloWorld'
        instance = Instance.create(app, 'default_device_name')
        existing_actions = {'helloWorld': instance().helloWorld,
                            'repeatBackToMe': instance().repeatBackToMe,
                            'returnPlusOne': instance().returnPlusOne}
        for action, function in existing_actions.items():
            self.assertEqual(load_app_function(instance(), action), function)

    def test_load_app_function_invalid_function(self):
        instance = Instance.create('HelloWorld', 'default_device_name')
        self.assertIsNone(load_app_function(instance(), 'JunkFunctionName'))

    def test_load_workflows(self):
        expected_workflows = ['basicWorkflowTest.workflow',
                              'loopWorkflow.workflow',
                              'multiactionWorkflowTest.workflow',
                              'multistepError.workflow',
                              'simpleDataManipulationWorkflow.workflow',
                              'templatedWorkflowTest.workflow',
                              'testExecutionWorkflow.workflow',
                              'testScheduler.workflow',
                              'tieredWorkflow.workflow']
        received_workflows = locate_workflows_in_directory(testWorkflowsPath)
        self.assertEqual(len(received_workflows), len(expected_workflows))
        self.assertSetEqual(set(received_workflows), set(expected_workflows))