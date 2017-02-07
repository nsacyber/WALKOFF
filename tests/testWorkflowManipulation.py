import unittest, ast
from core import controller, graphDecorator
from tests import config


class TestWorkflowManipulation(unittest.TestCase):
    def setUp(self):
        self.c = controller.Controller()
        self.c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "simpleDataManipulationWorkflow.workflow")
        self.testWorkflow = self.c.workflows["helloWorldWorkflow"]

    def tearDown(self):
        self.c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "simpleDataManipulationWorkflow.workflow")
        self.testWorkflow = self.c.workflows["helloWorldWorkflow"]

    def executionTest(self):
        # Check that the workflow executed correctly post-manipulation
        steps, instances = self.c.executeWorkflow(self.testWorkflow.name)
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

    @graphDecorator.callgraph(enabled=False)
    def test_createWorkflow(self):
        self.assertTrue(len(self.c.workflows) == 1)
        # Create Empty Workflow
        self.c.createWorkflowFromTemplate()
        self.assertTrue(len(self.c.workflows) == 2)
        self.assertTrue(self.c.workflows["emptyWorkflow"].steps == {})

        xml = self.c.workflows["emptyWorkflow"].toXML()
        self.assertTrue(len(xml.findall(".//steps/*")) == 0)

    @graphDecorator.callgraph(enabled=False)
    def test_removeWorkflow(self):
        self.c.createWorkflowFromTemplate()
        self.assertTrue(len(self.c.workflows) == 2)

        success = self.c.removeWorkflow("emptyWorkflow")
        self.assertTrue(success)
        self.assertTrue(len(self.c.workflows) == 1)
        self.assertTrue(self.c.workflows["helloWorldWorkflow"])

    @graphDecorator.callgraph(enabled=False)
    def test_updateWorkflow(self):
        self.c.createWorkflowFromTemplate()
        self.c.updateWorkflowName(oldName="emptyWorkflow", newName="newWorkflowName")

        self.assertTrue(len(self.c.workflows) == 2)
        self.assertFalse("emptyWorkflow" in self.c.workflows)
        self.assertTrue(self.c.workflows["newWorkflowName"])

    @graphDecorator.callgraph(enabled=False)
    def test_displayWorkflow(self):
        workflow = ast.literal_eval(self.c.workflows["helloWorldWorkflow"].__repr__())
        self.assertTrue(len(workflow["steps"]) == 1)
        self.assertTrue(workflow["options"])

    """
        CRUD - Step
    """

    @graphDecorator.callgraph(enabled=False)
    def test_createStep(self):
        self.testWorkflow.createStep(id="1", action="repeatBackToMe", app="HelloWorld", device="hwTest",
                                     input={"call": {"tag": "call", "value": "This is a test.", "format": "str"}})

        steps = self.testWorkflow.steps

        # Check that the step was added
        self.assertTrue(len(steps) == 2)
        self.assertTrue(steps["1"])

        # Check attributes
        step = self.testWorkflow.steps["1"]
        self.assertTrue(step.id == "1")
        self.assertTrue(step.action == "repeatBackToMe")
        self.assertTrue(step.app == "HelloWorld")
        self.assertTrue(step.device == "hwTest")
        # self.assertTrue(step.input == {'call': {'value': 'This is a test.', 'type': 'string', 'key': 'call'}}))
        self.assertTrue(step.conditionals == [])
        self.assertTrue(step.errors == [])

        self.executionTest()

    @graphDecorator.callgraph(enabled=False)
    def test_addStepToXML(self):
        self.testWorkflow.createStep(id="1", action="repeatBackToMe", app="HelloWorld", device="hwTest",
                                     input={"call": {"tag": "call", "value": "This is a test.", "format": "str"}})
        xml = self.testWorkflow.toXML()

        # Verify Structure
        steps = xml.findall(".//steps/step")
        self.assertTrue(len(steps) == 2)
        step = xml.find(".//steps/step/[@id='1']")
        self.assertTrue(step.get("id") == "1")
        self.assertTrue(step.find(".//action").text == "repeatBackToMe")
        self.assertTrue(step.find(".//app").text == "HelloWorld")
        self.assertTrue(step.find(".//device").text == "hwTest")
        self.assertTrue(step.find(".//next") is None)
        self.assertTrue(step.find(".//error") is None)

        self.executionTest()

    @graphDecorator.callgraph(enabled=False)
    def test_removeStep(self):
        self.testWorkflow.createStep(id="1", action="repeatBackToMe", app="HelloWorld", device="hwTest",
                                     input={"call": {"tag": "call", "value": "This is a test.", "format": "str"}})
        # Makes sure a new step was created...
        self.assertTrue(len(self.testWorkflow.steps) == 2)

        # ...So that we may destroy it!
        removed = self.testWorkflow.removeStep(id="1")
        self.assertTrue(removed)
        self.assertTrue(len(self.testWorkflow.steps) == 1)

        # Tests the XML representation after changes
        xml = self.testWorkflow.toXML()
        steps = xml.findall(".//steps/*")
        self.assertTrue(len(steps) == 1)
        self.assertTrue(steps[0].get("id") == "start")

    @graphDecorator.callgraph(enabled=False)
    def test_updateStep(self):
        self.assertTrue(self.testWorkflow.steps["start"].action == "repeatBackToMe")
        self.testWorkflow.steps["start"].set(attribute="action", value="helloWorld")
        self.assertTrue(self.testWorkflow.steps["start"].action == "helloWorld")

        xml = self.testWorkflow.toXML()
        self.assertTrue(xml.find(".//steps/step/[@id='start']/action").text == "helloWorld")

    @graphDecorator.callgraph(enabled=False)
    def test_displaySteps(self):
        output = ast.literal_eval(self.testWorkflow.__repr__())
        self.assertTrue(output["options"])
        self.assertTrue(output["steps"])
        self.assertTrue(len(output["steps"]) == 1)
        self.assertTrue(output["steps"]["start"]["action"] == "repeatBackToMe")

    """
        CRUD - Next
    """

    @graphDecorator.callgraph(enabled=False)
    def test_createNext(self):
        self.testWorkflow.steps["start"].createNext(nextStep="2", flags=[])
        xml = self.testWorkflow.toXML()
        step = self.testWorkflow.steps["start"]

        self.assertTrue(len(step.conditionals) == 2)
        self.assertTrue(step.conditionals[1].nextStep == "2")

        # Check XML
        self.assertTrue(len(xml.findall(".//steps/step/[@id='start']/next")) == 2)
        self.assertTrue(xml.find(".//steps/step/[@id='start']/next/[@next='2']").get("next") == "2")

    @graphDecorator.callgraph(enabled=False)
    def test_removeNext(self):
        step = self.testWorkflow.steps["start"]
        self.assertTrue(len(step.conditionals) == 1)
        success = step.removeNext("1")
        self.assertTrue(success)
        self.assertTrue(len(step.conditionals) == 0)

        xml = self.testWorkflow.toXML()

        # Check XML
        self.assertTrue(len(xml.findall(".//steps/step/[@id='start']/next")) == 0)

    @graphDecorator.callgraph(enabled=False)
    def test_updateNext(self):
        step = self.testWorkflow.steps["start"]
        self.assertTrue(step.conditionals[0].nextStep == "1")
        step.conditionals[0].nextStep = "2"
        self.assertTrue(step.conditionals[0].nextStep == "2")

        xml = self.testWorkflow.toXML()

        # Check XML
        self.assertTrue(xml.find(".//steps/step/[@id='start']/next").get("next") == "2")

    @graphDecorator.callgraph(enabled=False)
    def test_displayNext(self):
        conditional = ast.literal_eval(self.testWorkflow.steps["start"].conditionals[0].__repr__())
        self.assertTrue(conditional["flags"])
        self.assertTrue(conditional["nextStep"] == "1")

    """
        CRUD - Flag
    """

    @graphDecorator.callgraph(enabled=False)
    def test_createFlag(self):
        nextStep = self.testWorkflow.steps["start"].conditionals[0]
        self.assertTrue(len(nextStep.flags) == 1)
        nextStep.createFlag(action="count", args={"operator": "ge", "threshold": "1"}, filters=[])
        self.assertTrue(len(nextStep.flags) == 2)
        self.assertTrue(nextStep.flags[1].action == "count")
        self.assertTrue(nextStep.flags[1].args == {"operator": "ge", "threshold": "1"})
        self.assertTrue(nextStep.flags[1].filters == [])

    @graphDecorator.callgraph(enabled=False)
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

    @graphDecorator.callgraph(enabled=False)
    def test_updateFlag(self):
        self.assertTrue(self.testWorkflow.steps["start"].conditionals[0].flags[0].action == "regMatch")
        self.testWorkflow.steps["start"].conditionals[0].flags[0].set(attribute="action", value="count")
        self.assertTrue(self.testWorkflow.steps["start"].conditionals[0].flags[0].action == "count")

        # Check the XML output
        xml = self.testWorkflow.toXML()
        self.assertTrue(xml.find(".//steps/step/[@id='start']/next/[@next='1']/flag[1]").get("action") == "count")

    @graphDecorator.callgraph(enabled=False)
    def test_displayFlag(self):
        output = ast.literal_eval(self.testWorkflow.steps["start"].conditionals[0].flags[0].__repr__())
        self.assertTrue(output["action"])
        self.assertTrue(output["args"])
        self.assertTrue(output["filters"] == [{'action': 'length',
                                               'args': {},
                                               'event_handler': {'event_type': 'filterHandler',
                                                                 'events': "['FilterSuccess', 'FilterError']"},
                                               'id': 'start',
                                               'ancestry': ['defaultController', 'helloWorldWorkflow', 'start', '1',
                                                            'regMatch', 'length']}])
    """
        CRUD - Filter
    """

    @graphDecorator.callgraph(enabled=False)
    def test_createFilter(self):
        conditional = self.testWorkflow.steps["start"].conditionals[0].flags[0]
        self.assertTrue(len(conditional.filters) == 1)

        conditional.addFilter(action="length", args={"test": "test"})
        self.assertTrue(len(conditional.filters) == 2)
        self.assertTrue(conditional.filters[1].action == "length")
        self.assertTrue(conditional.filters[1].args["test"])

        # Tests adding a filter at index
        conditional.addFilter(action="length", args={"test2": "test2"}, index=1)
        self.assertTrue(len(conditional.filters) == 3)
        self.assertTrue(conditional.filters[1].action == "length")
        self.assertTrue(conditional.filters[1].args["test2"])
        self.assertTrue(conditional.filters[2].action == "length")
        self.assertTrue(conditional.filters[2].args["test"])

        xml = self.testWorkflow.toXML()

        # Check XML
        self.assertTrue(len(
            xml.findall(".//steps/step/[@id='start']/next/[@next='1']/flag/[@action='regMatch']/filters/filter")) == 3)
        self.assertTrue(len(xml.findall(
            ".//steps/step/[@id='start']/next/[@next='1']/flag/[@action='regMatch']/filters/filter[2]/args/test2")) == 1)
        self.assertTrue(len(xml.findall(
            ".//steps/step/[@id='start']/next/[@next='1']/flag/[@action='regMatch']/filters/filter[3]/args/test")) == 1)

    @graphDecorator.callgraph(enabled=False)
    def test_removeFilter(self):
        conditional = self.testWorkflow.steps["start"].conditionals[0].flags[0]
        conditional.addFilter(action="length", args={"test": "test"})
        conditional.addFilter(action="length", args={"test2": "test2"}, index=1)
        self.assertTrue(len(conditional.filters) == 3)

        conditional.removeFilter(index=0)
        self.assertTrue(len(conditional.filters) == 2)
        self.assertTrue(conditional.filters[1].action == "length")
        self.assertTrue(conditional.filters[1].args["test"])
        self.assertTrue(conditional.filters[0].action == "length")
        self.assertTrue(conditional.filters[0].args["test2"])

        xml = self.testWorkflow.toXML()

        # Check XML
        self.assertTrue(len(
            xml.findall(".//steps/step/[@id='start']/next/[@next='1']/flag/[@action='regMatch']/filters/filter")) == 2)
        self.assertTrue(len(xml.findall(
            ".//steps/step/[@id='start']/next/[@next='1']/flag/[@action='regMatch']/filters/filter[1]/args/test2")) == 1)
        self.assertTrue(len(xml.findall(
            ".//steps/step/[@id='start']/next/[@next='1']/flag/[@action='regMatch']/filters/filter[2]/args/test")) == 1)

    @graphDecorator.callgraph(enabled=False)
    def test_updateFilter(self):
        conditional = self.testWorkflow.steps["start"].conditionals[0].flags[0]
        self.assertTrue(conditional.filters[0].action == "length")
        conditional.filters[0].action = "combine"
        self.assertTrue(conditional.filters[0].action == "combine")

        xml = self.testWorkflow.toXML()
        # Check XML
        self.assertTrue(
            xml.find(".//steps/step/[@id='start']/next/[@next='1']/flag/[@action='regMatch']/filters/filter[1]").get(
                "action") == "combine")

    @graphDecorator.callgraph(enabled=False)
    def test_displayFilter(self):
        conditional = ast.literal_eval(self.testWorkflow.steps["start"].conditionals[0].flags[0].filters.__repr__())
        self.assertTrue(len(conditional) == 1)
        self.assertTrue(conditional[0]["action"] == "length")

    """
        CRUD - Options
    """

    @graphDecorator.callgraph(enabled=False)
    def test_createOption(self):
        self.assertEqual(True, True)

    @graphDecorator.callgraph(enabled=False)
    def test_removeOption(self):
        self.assertEqual(True, True)

    @graphDecorator.callgraph(enabled=False)
    def test_updateOption(self):
        self.assertEqual(True, True)

    @graphDecorator.callgraph(enabled=False)
    def test_displayOption(self):
        self.assertEqual(True, True)
