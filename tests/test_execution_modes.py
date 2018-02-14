import time
import unittest

import walkoff.appgateway
import walkoff.case.database as case_database
import walkoff.case.subscription as case_subscription
import walkoff.config.config
import walkoff.config.config
from walkoff.core.scheduler import scheduler
from walkoff.events import WalkoffEvent, EventType
from tests import config
import walkoff.config.paths
from tests.util import device_db_help


class TestExecutionModes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        device_db_help.setup_dbs()
        walkoff.appgateway.cache_apps(config.test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=config.test_apps_path)

    def setUp(self):
        case_database.initialize()

    def tearDown(self):
        device_db_help.cleanup_device_db()

        case_database.case_db.session.query(case_database.Event).delete()
        case_database.case_db.session.query(case_database.Case).delete()
        case_database.case_db.session.commit()
        case_database.case_db.tear_down()

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()
        device_db_help.tear_down_device_db()

    def test_start_stop_execution_loop(self):
        device_db_help.load_playbook('testScheduler')
        subs = {'controller': [event.signal_name for event in WalkoffEvent if event.event_type == EventType.controller]}
        case_subscription.set_subscriptions({'case1': subs})
        scheduler.start()
        time.sleep(0.1)
        scheduler.stop(wait=False)

        start_stop_event_history = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'case1').first().events.all()
        self.assertEqual(len(start_stop_event_history), 2,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(2, len(start_stop_event_history)))

    def test_pause_resume_scheduler_execution(self):
        device_db_help.load_playbook('testScheduler')

        subs = {'controller': [event.signal_name for event in WalkoffEvent if event.event_type == EventType.controller]}
        case_subscription.set_subscriptions({'pauseResume': subs})

        scheduler.start()
        scheduler.pause()
        time.sleep(0.1)
        scheduler.resume()
        time.sleep(0.1)
        scheduler.stop(wait=False)

        pause_resume_event_history = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'pauseResume').first().events.all()

        self.assertEqual(len(pause_resume_event_history), 4,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(4, len(pause_resume_event_history)))
