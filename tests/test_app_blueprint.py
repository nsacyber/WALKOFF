from server.returncodes import *
from tests.util.servertestcase import ServerTestCase


class TestAppBlueprint(ServerTestCase):

    def test_basic_blueprint(self):
        response = self.app.get('/apps/HelloWorld/test_blueprint', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = response.get_data(as_text=True)
        self.assertEqual(response, 'successfully called basic blueprint')

    def test_templated_blueprint(self):
        response = self.app.get('/apps/HelloWorld/test_action/test_action_blueprint', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = response.get_data(as_text=True)
        self.assertEqual(response, 'successfully called templated blueprint with action test_action')

    def test_basic_widget_blueprint(self):
        response = self.app.get('/apps/HelloWorld/testWidget/test_blueprint', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = response.get_data(as_text=True)
        self.assertEqual(response, 'successfully called basic blueprint')

    def test_templated_widget_blueprint(self):
        response = self.app.get('/apps/HelloWorld/testWidget/test_action/test_action_blueprint', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = response.get_data(as_text=True)
        self.assertEqual(response, 'successfully called templated blueprint with action test_action')
