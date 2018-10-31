import unittest

import walkoff.appgateway
from tests.util import execution_db_help
from tests.util import initialize_test_config
from walkoff.executiondb.environment_variable import EnvironmentVariable


class TestAction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_test_config()
        execution_db_help.setup_dbs()

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()
        execution_db_help.tear_down_execution_db()

    def __compare_init(self, elem, name, value, description):
        self.assertEqual(elem.name, name)
        self.assertEqual(elem.value, value)
        self.assertEqual(elem.description, description)

    def test_init_default(self):
        env_var = EnvironmentVariable(name='test_name', value='test_value', description='test_description')
        self.__compare_init(env_var, 'test_name', 'test_value', 'test_description')
