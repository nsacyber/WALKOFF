from tests.util.servertestcase import ServerTestCase


class TestHealthEndpoint(ServerTestCase):

    def test_endpoint(self):
        response = self.get_with_status_check('/health', status_code=200)
        expected_checks = {
            'check_cache',
            'check_server_db',
            'check_execution_db'
        }
        self.assertEqual(response['status'], 'success')
        checks = {result['checker'] for result in response['results']}
        self.assertSetEqual(checks, expected_checks)
        self.assertTrue(all(result['passed'] for result in response['results']))
