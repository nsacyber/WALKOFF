from apscheduler.schedulers.base import STATE_PAUSED, STATE_RUNNING, STATE_STOPPED
from tests.util.servertestcase import ServerTestCase
import json
from server.returncodes import *


class TestSchedulerActions(ServerTestCase):

    def test_scheduler_actions(self):
        response = self.app.get('/api/scheduler/start', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertIn('status', response)
        self.assertEqual(STATE_RUNNING, response['status'])

        response = self.app.get('/api/scheduler/start', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertIn('status', response)
        self.assertEqual("Scheduler already running.", response['status'])

        response = self.app.get('/api/scheduler/pause', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertIn('status', response)
        self.assertEqual(STATE_PAUSED, response['status'])

        response = self.app.get('/api/scheduler/pause', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertIn('status', response)
        self.assertEqual("Scheduler already paused.", response['status'])

        response = self.app.get('/api/scheduler/resume', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertIn('status', response)
        self.assertEqual(STATE_RUNNING, response['status'])

        response = self.app.get('/api/scheduler/resume', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertIn('status', response)
        self.assertEqual("Scheduler is not in PAUSED state and cannot be resumed.", response['status'])

        response = self.app.get('/api/scheduler/stop', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertIn('status', response)
        self.assertEqual(STATE_STOPPED, response['status'])

        response = self.app.get('/api/scheduler/stop', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertIn('status', response)
        self.assertEqual("Scheduler already stopped.", response['status'])
