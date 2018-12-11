from os import sep
from os.path import join, abspath

import walkoff.config
from walkoff.helpers import format_db_path


class TestConfig(walkoff.config.Config):
    CONFIG_PATH = join('.', 'tests', 'tmp', 'config.json')
    TEST_PATH = join('.', 'tests')
    WORKFLOWS_PATH = join('.', 'tests', 'testWorkflows') + sep
    APPS_PATH = join('.', 'tests', 'testapps')
    DATA_DIR_NAME = 'testdata'
    DATA_PATH = join('.', 'tests', DATA_DIR_NAME)
    DEFAULT_APPDEVICE_EXPORT_PATH = join(DATA_PATH, 'appdevice.json')
    DEFAULT_CASE_EXPORT_PATH = join(DATA_PATH, 'cases.json')
    BASIC_APP_API = join('.', 'tests', 'schemas', 'basic_app_api.yaml')
    CACHE_PATH = join('.', 'tests', 'tmp', 'cache')
    DB_PATH = abspath(join('.', 'tests', 'tmp', 'walkoff_test.db'))
    EXECUTION_DB_PATH = abspath(join('.', 'tests', 'tmp', 'execution_test.db'))
    NUMBER_PROCESSES = 2
    CACHE = {'type': 'redis', 'host': 'localhost', 'port': 6379}
    WALKOFF_DB_TYPE = 'sqlite'
    SQLALCHEMY_DATABASE_URI = format_db_path(WALKOFF_DB_TYPE, DB_PATH)
