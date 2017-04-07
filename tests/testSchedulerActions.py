import json
import unittest

from apscheduler.schedulers.base import STATE_PAUSED, STATE_RUNNING, STATE_STOPPED

from server import flaskServer as server

class TestUsersAndRoles(unittest.TestCase):
    def setUp(self):
        self.app = server.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        response = self.app.post('/key', data=dict(email='admin', password='admin'), follow_redirects=True).get_data(as_text=True)

        self.key = json.loads(response)["auth_token"]
        self.headers = {"Authentication-Token" : self.key}


    def tearDown(self):
        pass

    def testSchedulerActions(self):
        response = json.loads(self.app.post('/execution/scheduler/start', headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["status"], STATE_RUNNING)

        response = json.loads(self.app.post('/execution/scheduler/pause', headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["status"], STATE_PAUSED)

        response = json.loads(self.app.post('/execution/scheduler/resume', headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["status"], STATE_RUNNING)

        response = json.loads(self.app.post('/execution/scheduler/stop', headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["status"], STATE_STOPPED)
