import unittest, time
from core import controller, case

class TestExecutionModes(unittest.TestCase):
    def test_startStopExecutionLoop(self):
        c = controller.Controller(name="startStopController")
        c.loadWorkflowsFromFile(path="tests/testWorkflows/testScheduler.workflow")

        case.addCase(name="startStop", case=case.Case(subscriptions={
            "startStopController": ["schedulerStart", "schedulerShutdown", "schedulerPaused", "schedulerResumed", "jobAdded",
                                    "jobRemoved", "jobExecuted", "jobException"]
            }, history=[]))
        history = case.cases["startStop"]
        with history:
            c.start()
            time.sleep(1)
            c.stop(wait=False)
            self.assertTrue(len(history.history) == 2)

    def test_pauseResumeSchedulerExecution(self):
        c = controller.Controller(name="pauseResumeController")
        c.loadWorkflowsFromFile(path="tests/testWorkflows/testScheduler.workflow")

        case.addCase(name="pauseResume", case=case.Case(subscriptions={
            "pauseResumeController": ["schedulerStart", "schedulerShutdown", "schedulerPaused", "schedulerResumed", "jobAdded",
                       "jobRemoved", "jobExecuted", "jobException"]
            }, history=[]))

        history = case.cases["pauseResume"]

        with history:
            c.start()
            c.pause()
            time.sleep(1)
            c.resume()
            time.sleep(1)
            c.stop(wait=False)
            self.assertTrue(len(history.history) == 4)









