import unittest, time

from core import controller

class TestExecutionModes(unittest.TestCase):
    def setUp(self):
        pass

    def test_startStopExecutionLoop(self):
        self.c = controller.Controller()
        self.c.loadWorkflowsFromFile(path="tests/testWorkflows/testScheduler.workflow")

        self.c.start()
        time.sleep(3)
        self.c.stop()
        self.assertTrue(len(self.c.eventLog) == 3)

    def test_pauseResumeSchedulerExecution(self):
        self.c = controller.Controller()
        self.c.loadWorkflowsFromFile(path="tests/testWorkflows/testScheduler.workflow")
        self.c.start()
        self.c.pause()
        time.sleep(3)
        self.c.resume()
        time.sleep(3)
        self.c.stop()
        self.assertTrue(len(self.c.eventLog) == 6)









