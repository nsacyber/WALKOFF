import json

from apscheduler.schedulers.base import STATE_PAUSED, STATE_RUNNING, STATE_STOPPED

from tests.util.servertestcase import ServerTestCase
from walkoff.server.returncodes import *


class TestSchedulerActions(ServerTestCase):

    def take_action(self, action):
        data = {'status': action}
        return self.put_with_status_check('/api/scheduler', headers=self.headers, data=json.dumps(data),
                                          status_code=SUCCESS, content_type='application/json')

    def assert_status_equal(self, response, status):
        self.assertIn('status', response)
        self.assertEqual(status, response['status'])

    def test_scheduler_actions(self):
        response = self.take_action('start')
        self.assert_status_equal(response, STATE_RUNNING)

        response = self.take_action('start')
        self.assertEqual("Scheduler already running.", response['status'])

        response = self.take_action('pause')
        self.assertEqual(STATE_PAUSED, response['status'])

        response = self.take_action('pause')
        self.assertEqual("Scheduler already paused.", response['status'])

        response = self.take_action('resume')
        self.assertEqual(STATE_RUNNING, response['status'])

        response = self.take_action('resume')
        self.assertEqual("Scheduler is not in PAUSED state and cannot be resumed.", response['status'])

        response = self.take_action('stop')
        self.assertEqual(STATE_STOPPED, response['status'])

        response = self.take_action('stop')
        self.assertEqual("Scheduler already stopped.", response['status'])

    def test_update_scheduler_status_invalid_status(self):
        data = {'status': 'invalid'}
        self.put_with_status_check('/api/scheduler', headers=self.headers, data=json.dumps(data),
                                   status_code=BAD_REQUEST, content_type='application/json')
