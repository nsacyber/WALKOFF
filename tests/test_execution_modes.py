import time
import unittest

import walkoff.appgateway
import walkoff.case.database as case_database
import walkoff.case.subscription as case_subscription
import walkoff.config.config
import walkoff.config.config
from walkoff import controller
from walkoff.events import WalkoffEvent, EventType
from tests import config
import walkoff.config.paths
from walkoff import initialize_databases


class TestExecutionModes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        walkoff.config.paths.db_path = config.test_db_path
        walkoff.config.paths.case_db_path = config.test_case_db_path
        walkoff.config.paths.device_db_path = config.test_device_db_path
        initialize_databases()
        walkoff.appgateway.cache_apps(config.test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=config.test_apps_path)

    def setUp(self):
        case_database.initialize()

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()

    def test_start_stop_execution_loop(self):
        c = controller.Controller()
        # c.load_playbook(resource=config.test_workflows_path + "testScheduler.playbook")
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
        # c.load_playbook(resource=config.test_workflows_path + "testScheduler.playbook")

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
