import unittest
import json

from server import flaskServer as server
from tests.util.assertwrappers import orderless_list_compare
from tests.config import test_apps_path
import core.config.paths


class TestLogin(unittest.TestCase):
    def setUp(self):
        self.app = server.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)

        response = self.app.post('/key', data=dict(email='admin', password='admin'),
                                 follow_redirects=True).get_data(as_text=True)
        core.config.paths.apps_path = test_apps_path

        self.key = json.loads(response)["auth_token"]
        self.headers = {"Authentication-Token": self.key}

    def test_login(self):
        response = self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_list_apps(self):
        expected_apps = ['HelloWorld']
        response = self.app.get('/apps/', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        orderless_list_compare(self, response['apps'], expected_apps)

    def test_get_all_list_actions(self):
        expected_json = {"HelloWorld": ['helloWorld', 'repeatBackToMe', 'returnPlusOne', 'pause']}
        response = self.app.get('/apps/actions', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        orderless_list_compare(self, response.keys(), expected_json.keys())
        for app, functions in response.items():
            orderless_list_compare(self, functions, expected_json[app])
