import unittest, ast

from core import controller

class TestWorkflowManipulation(unittest.TestCase):
    def setUp(self):
        self.c = controller.Controller()
        self.c.loadWorkflowsFromFile(path="tests/testWorkflows/simpleDataManipulationWorkflow.workflow")
        self.testWorkflow = self.c.workflows["helloWorldWorkflow"]

    def tearDown(self):
        self.c.loadWorkflowsFromFile(path="tests/testWorkflows/simpleDataManipulationWorkflow.workflow")
        self.testWorkflow = self.c.workflows["helloWorldWorkflow"]

    def executionTest(self):
        # Check that the workflow executed correctly post-manipulation
        steps, instances = self.testWorkflow.execute()
        instances = ast.literal_eval(instances)
        self.assertTrue(len(steps) == 2)
        self.assertTrue(len(instances) == 1)
        self.assertTrue(steps[0].id == "start")
        self.assertTrue(steps[0].output == "REPEATING: Hello World")
        self.assertTrue(steps[1].id == "1")
        self.assertTrue(steps[1].output == "REPEATING: This is a test.")
    """
        CRUD - Workflow
    """
    def test_createWorkflow(self):
        pass

    def test_removeWorkflow(self):
        pass

    def test_updateWorkflow(self):
        pass

    def test_displayWorkflow(self):
        pass

    """
        CRUD - Step
    """
    def test_createStep(self):
        self.testWorkflow.createStep(id="1", action="repeatBackToMe", app="HelloWorld", device="hwTest",
                                     input={"call":{"tag":"call", "value":"This is a test.", "format":"string"}})

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
        self.assertTrue(step.conditionals == [])
        self.assertTrue(step.errors == [])

        self.executionTest()

    def test_addStepToXML(self):
        self.testWorkflow.createStep(id="1", action="repeatBackToMe", app="HelloWorld", device="hwTest",
                                     input={"call": {"tag": "call", "value": "This is a test.", "format": "string"}})

        xml = self.testWorkflow.toXML()

        #Verify Structure
        steps = xml.findall(".//steps/step")
        self.assertTrue(len(steps) == 2)
        step = xml.find(".//steps/step/[@id='1']")
        self.assertTrue(step.get("id") == "1")
        self.assertTrue(step.find(".//action").text == "repeatBackToMe")
        self.assertTrue(step.find(".//app").text == "HelloWorld")
        self.assertTrue(step.find(".//device").text == "hwTest")
        #self.assertTrue(et.dump(step.find(".//input")) == "<input><call format=\"string\">This is a test.</call></input>")
        self.assertTrue(step.find(".//next") == None)
        self.assertTrue(step.find(".//error") == None)

        self.executionTest()

    def test_removeStep(self):
        self.testWorkflow.createStep(id="1", action="repeatBackToMe", app="HelloWorld", device="hwTest",
                                     input={"call": {"tag": "call", "value": "This is a test.", "format": "string"}})
        #Makes sure a new step was created...
        self.assertTrue(len(self.testWorkflow.steps) == 2)

        #...So that we may destroy it!
        removed = self.testWorkflow.removeStep(id="1")
        self.assertTrue(removed)
        self.assertTrue(len(self.testWorkflow.steps) == 1)

        #Tests the XML representation after changes
        xml = self.testWorkflow.toXML()
        steps = xml.findall(".//steps/*")
        self.assertTrue(len(steps) == 1)
        self.assertTrue(steps[0].get("id") == "start")

    def test_updateStep(self):
        self.assertTrue(self.testWorkflow.steps["start"].action == "repeatBackToMe")
        self.testWorkflow.steps["start"].set(attribute="action", value="helloWorld")
        self.assertTrue(self.testWorkflow.steps["start"].action == "helloWorld")

        xml = self.testWorkflow.toXML()
        self.assertTrue(xml.find(".//steps/step/[@id='start']/action").text == "helloWorld")

    def test_displaySteps(self):
        output = ast.literal_eval(self.testWorkflow.__repr__())
        self.assertTrue(output["options"])
        self.assertTrue(output["steps"])
        self.assertTrue(len(output["steps"]) == 1)
        self.assertTrue(output["steps"]["start"]["action"] == "repeatBackToMe")

    """
        CRUD - Next
    """

    def test_createNext(self):
        self.testWorkflow.steps["start"].createNext(nextStep="2", flags=[])
        xml = self.testWorkflow.toXML()
        step = self.testWorkflow.steps["start"]

        self.assertTrue(len(step.conditionals) == 2)
        self.assertTrue(step.conditionals[1].nextStep == "2")

        #Check XML
        self.assertTrue(len(xml.findall(".//steps/step/[@id='start']/next")) == 2)
        self.assertTrue(xml.find(".//steps/step/[@id='start']/next/[@next='2']").get("next") == "2")

    def test_removeNext(self):
        pass

    def test_updateNext(self):
        pass

    def test_displayNext(self):
        pass



    """
        CRUD - Flag
    """

    def test_createFlag(self):
        nextStep = self.testWorkflow.steps["start"].conditionals[0]
        self.assertTrue(len(nextStep.flags) == 1)
        nextStep.createFlag(action="count", args={"operator" : "ge", "threshold":"1"}, filters=[])
        self.assertTrue(len(nextStep.flags) == 2)
        self.assertTrue(nextStep.flags[1].action == "count")
        self.assertTrue(nextStep.flags[1].args == {"operator" : "ge", "threshold":"1"})
        self.assertTrue(nextStep.flags[1].filters == [])

    def test_removeFlag(self):
        nextStep = self.testWorkflow.steps["start"].conditionals[0]
        self.assertTrue(len(nextStep.flags) == 1)
        success = nextStep.removeFlag(index=0)
        self.assertTrue(success)
        self.assertTrue(len(nextStep.flags) == 0)

        # Tests the XML representation after changes
        xml = self.testWorkflow.toXML()
        step = xml.findall(".//steps/step/[@id='start']/next")

        nextStepFlagsXML = xml.find(".//steps/step/[@id='start']/next")
        self.assertTrue(len(nextStepFlagsXML) == 0)

    def test_updateFlag(self):
        self.assertTrue(self.testWorkflow.steps["start"].conditionals[0].flags[0].action == "regMatch")
        self.testWorkflow.steps["start"].conditionals[0].flags[0].set(attribute="action", value="count")
        self.assertTrue(self.testWorkflow.steps["start"].conditionals[0].flags[0].action == "count")

        #Check the XML output
        xml = self.testWorkflow.toXML()
        self.assertTrue(xml.find(".//steps/step/[@id='start']/next/[@next='1']/flag[1]").get("action") == "count")

    def test_displayFlag(self):
        output = ast.literal_eval(self.testWorkflow.steps["start"].conditionals[0].flags[0].__repr__())
        self.assertTrue(output["action"])
        self.assertTrue(output["args"])
        self.assertTrue(output["filters"] == [{'action': 'length', 'args': {}}])

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






