import unittest, time
from core import controller, case, graphDecorator
from tests import config

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_SCHEDULER_START, \
    EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED
from core.case import Subscription


class TestExecutionModes(unittest.TestCase):
    def setUp(self):
        case.initialize_case_db()

    def tearDown(self):
        case.case_database.session.rollback()

    @graphDecorator.callgraph(enabled=False)
    def test_startStopExecutionLoop(self):
        c = controller.Controller(name="startStopController")
        c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "testScheduler.workflow")
        subs = {'startStopController': Subscription(events=[EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN,
                                                            EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED,
                                                            EVENT_JOB_ADDED, EVENT_JOB_REMOVED,
                                                            EVENT_JOB_EXECUTED, EVENT_JOB_ERROR])}
        case.set_subscriptions({'startStop': case.CaseSubscriptions(subscriptions=subs)})

        c.start()
        time.sleep(1)
        c.stop(wait=False)

        start_stop_event_history = case.case_database.session.query(case.Cases) \
            .filter(case.Cases.name == 'startStop').first().events.all()
        self.assertTrue(len(start_stop_event_history) == 2)

    @graphDecorator.callgraph(enabled=False)
    def test_pauseResumeSchedulerExecution(self):
        c = controller.Controller(name="pauseResumeController")
        c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "testScheduler.workflow")

        subs = {'pauseResumeController': Subscription(events=[EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN,
                                                              EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED,
                                                              EVENT_JOB_ADDED, EVENT_JOB_REMOVED,
                                                              EVENT_JOB_EXECUTED, EVENT_JOB_ERROR])}
        case.set_subscriptions({'startStop': case.CaseSubscriptions(subscriptions=subs)})
        case.set_subscriptions({'pauseResume': case.CaseSubscriptions(subscriptions=subs)})

        c.start()
        c.pause()
        time.sleep(1)
        c.resume()
        time.sleep(1)
        c.stop(wait=False)

        pause_resume_events_case = case.case_database.session.query(case.Cases) \
            .filter(case.Cases.name == 'pauseResume').first()
        pause_resume_event_history = pause_resume_events_case.events.all()
        self.assertTrue(len(pause_resume_event_history) == 4)
