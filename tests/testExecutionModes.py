import unittest, time

from core import controller

class TestExecutionModes(unittest.TestCase):
    def setUp(self):
        pass

    def test_startStopExecutionLoop(self):
        self.c = controller.Controller()
        self.c.loadWorkflowsFromFile(path="tests/testWorkflows/simpleDataManipulationWorkflow.workflow")
        self.c.startActiveExecution()

        self.assertTrue(self.c.status.value == 1)
        self.assertFalse(self.c.mainProcess == None)

        time.sleep(3)
        self.c.stopActiveExecution()

        self.assertTrue(self.c.status.value == 0)
        #self.assertTrue(self.c.mainProcess == None)

        #Check Output
        output = []
        while not self.c.executionLog.empty():
            output.extend(self.c.executionLog.get())
        self.assertTrue(len(output) == 1)
        self.assertTrue(output[0].output == "REPEATING: Hello World")




