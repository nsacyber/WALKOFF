import time
import unittest

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_SCHEDULER_START, \
    EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED

import apps
import core.case.database as case_database
import core.case.subscription as case_subscription
import core.config.config
from core.events import WalkoffEvent, EventType
from core import controller
from tests import config
import core.config.config


class TestExecutionModes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apps.cache_apps(config.test_apps_path)
        core.config.config.load_app_apis(apps_path=config.test_apps_path)

    def setUp(self):
        case_database.initialize()

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()

    def test_start_stop_execution_loop(self):
        c = controller.Controller()
        c.load_playbook(resource=config.test_workflows_path + "testScheduler.playbook")
        subs = {'controller': [event.signal_name for event in WalkoffEvent if event.event_type == EventType.controller]}
        case_subscription.set_subscriptions({'case1': subs})
        c.scheduler.start()
        time.sleep(0.1)
        c.scheduler.stop(wait=False)

        start_stop_event_history = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'case1').first().events.all()
        self.assertEqual(len(start_stop_event_history), 2,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(2, len(start_stop_event_history)))

    def test_pause_resume_scheduler_execution(self):
        c = controller.Controller()
        c.load_playbook(resource=config.test_workflows_path + "testScheduler.playbook")

        subs = {'controller': [event.signal_name for event in WalkoffEvent if event.event_type == EventType.controller]}
        case_subscription.set_subscriptions({'pauseResume': subs})

        c.scheduler.start()
        c.scheduler.pause()
        time.sleep(0.1)
        c.scheduler.resume()
        time.sleep(0.1)
        c.scheduler.stop(wait=False)

        pause_resume_event_history = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'pauseResume').first().events.all()

        self.assertEqual(len(pause_resume_event_history), 4,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(4, len(pause_resume_event_history)))
