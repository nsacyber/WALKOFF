import unittest
import json

from core.workflow import Workflow
from server import flaskServer as flask_server

class TestWorkflowServer(unittest.TestCase):
    def setUp(self):
        self.app = flask_server.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        response = self.app.post('/key', data=dict(email='admin', password='admin'),
                                 follow_redirects=True).get_data(as_text=True)

        self.key = json.loads(response)["auth_token"]
        self.headers = {"Authentication-Token": self.key}

    def test_display_workflows(self):
        expected_workflows = ['test']
        response = self.app.post('/workflow', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(expected_workflows), len(response['workflows']))
        self.assertSetEqual(set(expected_workflows), set(response['workflows']))


