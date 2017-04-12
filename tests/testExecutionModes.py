import time
import unittest

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_SCHEDULER_START, \
    EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED

import core.case.database as case_database
import core.case.subscription as case_subscription
from core import controller, graphdecorator
from core.case.subscription import Subscription
from tests import config


class TestExecutionModes(unittest.TestCase):
    def setUp(self):
        case_database.initialize()

    def tearDown(self):
        case_database.tear_down()

    @graphdecorator.callgraph(enabled=False)
    def test_startStopExecutionLoop(self):
        c = controller.Controller(name="startStopController")
        c.load_workflows_from_file(path=config.test_workflows_path + "testScheduler.workflow")
        subs = {'startStopController': Subscription(events=[EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN,
                                                            EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED,
                                                            EVENT_JOB_ADDED, EVENT_JOB_REMOVED,
                                                            EVENT_JOB_EXECUTED, EVENT_JOB_ERROR])}
        case_subscription.set_subscriptions({'startStop': case_subscription.CaseSubscriptions(subscriptions=subs)})
        c.start()
        time.sleep(1)
        c.stop(wait=False)

        start_stop_event_history = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'startStop').first().events.all()
        self.assertEqual(len(start_stop_event_history), 2,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(2, len(start_stop_event_history)))

    @graphdecorator.callgraph(enabled=False)
    def test_pauseResumeSchedulerExecution(self):
        c = controller.Controller(name="pauseResumeController")
        c.load_workflows_from_file(path=config.test_workflows_path + "testScheduler.workflow")

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

        pause_resume_events_case = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'pauseResume').first()
        pause_resume_event_history = pause_resume_events_case.events.all()

        self.assertEqual(len(pause_resume_event_history), 4,
                        'Incorrect length of event history. '
                        'Expected {0}, got {1}'.format(4, len(pause_resume_event_history)))
