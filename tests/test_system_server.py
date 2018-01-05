from tests.util.servertestcase import ServerTestCase
from walkoff.server.endpoints.system import humanize_bytes


class TestSystemServer(ServerTestCase):

    def test_humanize_bytes(self):
        self.assertEqual(humanize_bytes(1000), '1000B')
        self.assertEqual(humanize_bytes(1024), '1.0K')
        self.assertEqual(humanize_bytes(1000000000), '953.67M')

    def test_get_system_measurements(self):
        response = self.get_with_status_check('/api/system', headers=self.headers)
        self.assertSetEqual(set(response.keys()), {'cpu', 'memory', 'disk', 'net'})
