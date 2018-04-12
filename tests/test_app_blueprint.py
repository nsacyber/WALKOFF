from tests.util.servertestcase import ServerTestCase
from walkoff.server.returncodes import *


class TestAppBlueprint(ServerTestCase):
    def test_basic_blueprint(self):
        response = self.test_client.get('/interfaces/Sample/test_blueprint', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = response.get_data(as_text=True)
        self.assertEqual(response, 'successfully called basic blueprint')

    def test_templated_blueprint(self):
        response = self.test_client.get('/interfaces/Sample/test_action/test_action_blueprint', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = response.get_data(as_text=True)
        self.assertEqual(response, 'successfully called templated blueprint with action test_action')
