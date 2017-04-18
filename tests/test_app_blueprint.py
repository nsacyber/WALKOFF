from tests.util.assertwrappers import orderless_list_compare
from tests.util.servertestcase import ServerTestCase


class TestAppBlueprint(ServerTestCase):

    def test_list_functions(self):
        expected_actions = ['helloWorld', 'repeatBackToMe', 'returnPlusOne', 'pause']
        response = self.get_with_status_check('/apps/HelloWorld/actions', 'success', headers=self.headers)
        self.assertIn('actions', response)
        orderless_list_compare(self, response['actions'], expected_actions)

    def test_list_functions_invalid_name(self):
        self.get_with_status_check('/apps/JunkAppName/actions', 'error: app name not found', headers=self.headers)
