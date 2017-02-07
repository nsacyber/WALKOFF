import unittest, time
from core import controller, case, graphDecorator
from tests import config

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_SCHEDULER_START, \
    EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED
from core.case import Subscription

class TestExecutionModes(unittest.TestCase):
    @graphDecorator.callgraph(enabled=False)
    def test_startStopExecutionLoop(self):
        c = controller.Controller(name="startStopController")
        c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "testScheduler.workflow")
        subs = {'startStopController': Subscription(events=[EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN,
                                                            EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED,
                                                            EVENT_JOB_ADDED, EVENT_JOB_REMOVED,
                                                            EVENT_JOB_EXECUTED, EVENT_JOB_ERROR])}
        case.addCase(name="startStop", case=case.Case(subscriptions=subs, history=[]))
        history = case.cases["startStop"]
        with history:
            c.start()
            time.sleep(1)
            c.stop(wait=False)
            self.assertTrue(len(history.history) == 2)

    @graphDecorator.callgraph(enabled=False)
    def test_pauseResumeSchedulerExecution(self):
        c = controller.Controller(name="pauseResumeController")
        c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "testScheduler.workflow")

        subs = {'pauseResumeController': Subscription(events=[EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN,
                                                            EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED,
                                                            EVENT_JOB_ADDED, EVENT_JOB_REMOVED,
                                                            EVENT_JOB_EXECUTED, EVENT_JOB_ERROR])}
        case.addCase(name="pauseResume", case=case.Case(subscriptions=subs, history=[]))

        history = case.cases["pauseResume"]

        with history:
            c.start()
            c.pause()
            time.sleep(1)
            c.resume()
            time.sleep(1)
            c.stop(wait=False)
            self.assertTrue(len(history.history) == 4)

