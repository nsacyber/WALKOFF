import unittest, ast
from core import controller

class TestWorkflowManipulation(unittest.TestCase):
    def setUp(self):
        self.c = controller.Controller()
        self.c.loadWorkflowsFromFile(path="tests/testWorkflows/simpleDataManipulationWorkflow.workflow")
        self.testWorkflow = self.c.workflows["helloWorldWorkflow"]

    """
        CRUD - Step
    """

    def test_createStep(self):
        self.testWorkflow.createStep(id="1", action="repeatBackToMe", app="HelloWorld", device="hwTest", input={"call":{"tag":"call", "value":"This is a test.", "format":"string"}})
        steps = self.testWorkflow.steps

        #Check that the step was added
        self.assertTrue(len(steps) == 2)
        self.assertTrue(steps["1"])

        #Check attributes
        step = self.testWorkflow.steps["1"]
        self.assertTrue(step.id == "1")
        self.assertTrue(step.action == "repeatBackToMe")
        self.assertTrue(step.app == "HelloWorld")
        self.assertTrue(step.device == "hwTest")
        #self.assertTrue(step.input == {'call': {'value': 'This is a test.', 'type': 'string', 'key': 'call'}}))
        self.assertTrue(step.next == [])
        self.assertTrue(step.errors == [])

        #Check that the workflow executed correctly post-manipulation
        steps, instances = self.testWorkflow.execute()
        instances = ast.literal_eval(instances)
        self.assertTrue(len(steps) == 2)
        self.assertTrue(len(instances) == 1)
        self.assertTrue(steps[0].id == "start")
        self.assertTrue(steps[0].output == "REPEATING: Hello World")
        self.assertTrue(steps[1].id == "1")
        self.assertTrue(steps[1].output == "REPEATING: This is a test.")

    def test_addStepToXML(self):
        pass

    def test_removeStep(self):
        self.assertEqual(True, True)

    def test_updateStep(self):
        self.assertEqual(True, True)

    def test_displayStep(self):
        self.assertEqual(True, True)

    """
        CRUD - Flag
    """

    def test_createFlag(self):
        self.assertEqual(True, True)

    def test_removeFlag(self):
        self.assertEqual(True, True)

    def test_updateFlag(self):
        self.assertEqual(True, True)

    def test_displayFlag(self):
        self.assertEqual(True, True)

    """
        CRUD - Filter
    """

    def test_createFilter(self):
        self.assertEqual(True, True)

    def test_removeFilter(self):
        self.assertEqual(True, True)

    def test_updateFilter(self):
        self.assertEqual(True, True)

    def test_displayFilter(self):
        self.assertEqual(True, True)

    """
        CRUD - Options
    """

    def test_createOption(self):
        self.assertEqual(True, True)


    def test_removeOption(self):
        self.assertEqual(True, True)

    def test_updateOption(self):
        self.assertEqual(True, True)

    def test_displayOption(self):
        self.assertEqual(True, True)






