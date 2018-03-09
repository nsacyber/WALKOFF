import time
import unittest

import walkoff.appgateway
import walkoff.case.database as case_database
import walkoff.case.subscription as case_subscription
import walkoff.config.config
import walkoff.config.config
import walkoff.config.paths
from tests import config
from tests.util import execution_db_help
from walkoff.events import WalkoffEvent, EventType
from walkoff.scheduler import Scheduler
from walkoff.case.logger import CaseLogger
from mock import create_autospec


class TestExecutionModes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        execution_db_help.setup_dbs()
        walkoff.appgateway.cache_apps(config.test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=config.test_apps_path)
        mock_logger = create_autospec(CaseLogger)
        cls.scheduler = Scheduler(mock_logger)

    def setUp(self):
        case_database.initialize()

    def tearDown(self):
        execution_db_help.cleanup_device_db()

        case_database.case_db.session.query(case_database.Event).delete()
        case_database.case_db.session.query(case_database.Case).delete()
        case_database.case_db.session.commit()
        case_database.case_db.tear_down()

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()
        execution_db_help.tear_down_device_db()

    def test_start_stop_execution_loop(self):
        execution_db_help.load_playbook('testScheduler')
        subs = {'controller': [event.signal_name for event in WalkoffEvent if event.event_type == EventType.controller]}
        #case_subscription.set_subscriptions({'case1': subs})
        self.scheduler.start()
        time.sleep(0.1)
        self.scheduler.stop(wait=False)

        start_stop_event_history = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'case1').first().events.all()
        self.assertEqual(len(start_stop_event_history), 2,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(2, len(start_stop_event_history)))

    def test_pause_resume_scheduler_execution(self):
        execution_db_help.load_playbook('testScheduler')

        subs = {'controller': [event.signal_name for event in WalkoffEvent if event.event_type == EventType.controller]}
        #case_subscription.set_subscriptions({'pauseResume': subs})

        self.scheduler.start()
        self.scheduler.pause()
        time.sleep(0.1)
        self.scheduler.resume()
        time.sleep(0.1)
        self.scheduler.stop(wait=False)

        pause_resume_event_history = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'pauseResume').first().events.all()

        self.assertEqual(len(pause_resume_event_history), 4,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(4, len(pause_resume_event_history)))
