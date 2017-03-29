import unittest
import json
from server import flaskServer as flask_server
from tests.util.assertwrappers import orderless_list_compare
from tests.config import test_apps_path
import core.config.paths

class TestAppBlueprint(unittest.TestCase):
    def setUp(self):
        self.app = flask_server.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        response = self.app.post('/key', data=dict(email='admin', password='admin'),
                                 follow_redirects=True).get_data(as_text=True)
        core.config.paths.apps_path = test_apps_path
        self.key = json.loads(response)["auth_token"]
        self.headers = {"Authentication-Token": self.key}

    def test_list_functions(self):
        expected_actions = ['helloWorld', 'repeatBackToMe', 'returnPlusOne', 'pause']
        response = self.app.get('/apps/HelloWorld/actions', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertEqual(response['status'], 'success')
        orderless_list_compare(self, response['actions'], expected_actions)

    def test_list_functions_invalid_name(self):
        response = self.app.get('/apps/JunkAppName/actions', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertEqual(response['status'], 'error: app name not found')

    def test_function_aliases(self):
        expected_json = {"helloWorld": ["helloworld", "hello world", "hello", "greeting", "HelloWorld", "hello_world"],
                         "repeatBackToMe": ["parrot", "Parrot", "RepeatBackToMe", "repeat_back_to_me", "repeat"],
                         "returnPlusOne": ["plus one", "PlusOne", "plus_one", "plusone", "++", "increment"]}

        response = self.app.get('/apps/HelloWorld/actions/aliases', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, expected_json)