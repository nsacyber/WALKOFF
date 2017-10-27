from server.returncodes import *
from tests.util.assertwrappers import orderless_list_compare
from tests.util.servertestcase import ServerTestCase


class TestAppBlueprint(ServerTestCase):

    def test_list_functions(self):
        expected_actions = ['pause', 'Add Three', 'repeatBackToMe', 'Buggy',
                            'returnPlusOne', 'helloWorld', 'Hello World', 'Json Sample', 'Sample Event', 'global1', 'global2']
        response = self.get_with_status_check('/api/apps/HelloWorld/actions', headers=self.headers)
        self.assertIn('actions', response)
        orderless_list_compare(self, response['actions'], expected_actions)

    def test_list_functions_invalid_name(self):
        self.get_with_status_check('/api/apps/JunkAppName/actions',
                                   error='App name not found.',
                                   headers=self.headers,
                                   status_code=OBJECT_DNE_ERROR)

    def test_basic_blueprint(self):
        response = self.app.get('/apps/HelloWorld/test_blueprint', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = response.get_data(as_text=True)
        self.assertEqual(response, 'successfully called basic blueprint')

    def test_templated_blueprint(self):
        response = self.app.get('/apps/HelloWorld/test_action/test_action_blueprint', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = response.get_data(as_text=True)
        self.assertEqual(response, 'successfully called templated blueprint with action test_action')

    def test_basic_widget_blueprint(self):
        response = self.app.get('/apps/HelloWorld/testWidget/test_blueprint', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = response.get_data(as_text=True)
        self.assertEqual(response, 'successfully called basic blueprint')

    def test_templated_widget_blueprint(self):
        response = self.app.get('/apps/HelloWorld/testWidget/test_action/test_action_blueprint', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = response.get_data(as_text=True)
        self.assertEqual(response, 'successfully called templated blueprint with action test_action')
