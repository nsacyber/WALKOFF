import time
import unittest

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_SCHEDULER_START, \
    EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED

import core.case.database as case_database
import core.case.subscription as case_subscription
from core import controller, graphDecorator
from core.case.subscription import Subscription
from tests import config


class TestExecutionModes(unittest.TestCase):
    def setUp(self):
        case_database.initialize()

    def tearDown(self):
        case_database.case_db.session.rollback()

    @graphDecorator.callgraph(enabled=False)
    def test_startStopExecutionLoop(self):
        c = controller.Controller(name="startStopController")
        c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "testScheduler.workflow")
        subs = {'startStopController': Subscription(events=[EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN,
                                                            EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED,
                                                            EVENT_JOB_ADDED, EVENT_JOB_REMOVED,
                                                            EVENT_JOB_EXECUTED, EVENT_JOB_ERROR])}
        case_subscription.set_subscriptions({'startStop': case_subscription.CaseSubscriptions(subscriptions=subs)})
        c.start()
        time.sleep(1)
        c.stop(wait=False)

        start_stop_event_history = case_database.case_db.session.query(case_database.Cases) \
            .filter(case_database.Cases.name == 'startStop').first().events.all()
        self.assertTrue(len(start_stop_event_history) == 2)

    @graphDecorator.callgraph(enabled=False)
    def test_pauseResumeSchedulerExecution(self):
        c = controller.Controller(name="pauseResumeController")
        c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "testScheduler.workflow")

        subs = {'pauseResumeController': Subscription(events=[EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN,
                                                              EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED,
                                                              EVENT_JOB_ADDED, EVENT_JOB_REMOVED,
                                                              EVENT_JOB_EXECUTED, EVENT_JOB_ERROR])}
        case_subscription.set_subscriptions({'startStop': case_subscription.CaseSubscriptions(subscriptions=subs)})
        case_subscription.set_subscriptions({'pauseResume': case_subscription.CaseSubscriptions(subscriptions=subs)})

        c.start()
        c.pause()
        time.sleep(1)
        c.resume()
        time.sleep(1)
        c.stop(wait=False)

        pause_resume_events_case = case_database.case_db.session.query(case_database.Cases) \
            .filter(case_database.Cases.name == 'pauseResume').first()
        pause_resume_event_history = pause_resume_events_case.events.all()
        self.assertTrue(len(pause_resume_event_history) == 4)
