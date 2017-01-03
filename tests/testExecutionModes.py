import unittest, time

from core import controller

class TestExecutionModes(unittest.TestCase):
    def setUp(self):
        pass

    def test_startStopExecutionLoop(self):
        self.c = controller.Controller()
        self.c.loadWorkflowsFromFile(path="tests/testWorkflows/testScheduler.workflow")

        self.c.start()
        time.sleep(2)
        self.c.stop()
        self.assertTrue(len(self.c.eventLog) == 1)








