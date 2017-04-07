import json
import unittest

from apscheduler.schedulers.base import STATE_PAUSED, STATE_RUNNING, STATE_STOPPED

from server import flaskServer as server
from tests.util.assertwrappers import post_with_status_check


class TestSchedulerActions(unittest.TestCase):
    def setUp(self):
        self.app = server.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        response = self.app.post('/key', data=dict(email='admin', password='admin'),
                                 follow_redirects=True).get_data(as_text=True)

        self.key = json.loads(response)["auth_token"]
        self.headers = {"Authentication-Token": self.key}

    def test_scheduler_actions(self):
        post_with_status_check(self, self.app, '/execution/scheduler/start', STATE_RUNNING, headers=self.headers)
        post_with_status_check(self, self.app, '/execution/scheduler/start', STATE_RUNNING, headers=self.headers)

        post_with_status_check(self, self.app, '/execution/scheduler/pause', STATE_PAUSED, headers=self.headers)
        post_with_status_check(self, self.app, '/execution/scheduler/pause', STATE_PAUSED, headers=self.headers)

        post_with_status_check(self, self.app, '/execution/scheduler/resume', STATE_RUNNING, headers=self.headers)
        post_with_status_check(self, self.app, '/execution/scheduler/resume', STATE_RUNNING, headers=self.headers)

        post_with_status_check(self, self.app, '/execution/scheduler/stop', STATE_STOPPED, headers=self.headers)
        post_with_status_check(self, self.app, '/execution/scheduler/stop', STATE_STOPPED, headers=self.headers)
