from os import sep
from os.path import join
import walkoff.config


class TestConfig(walkoff.config.Config):
    CONFIG_PATH = join('.', 'tests', 'config.json')
    TEST_PATH = join('.', 'tests')
    WORKFLOWS_PATH = join('.', 'tests', 'testWorkflows') + sep
    APPS_PATH = join('.', 'tests', 'testapps')
    DATA_DIR_NAME = 'testdata'
    DATA_PATH = join('.', 'tests', DATA_DIR_NAME)
    DEFAULT_APPDEVICE_EXPORT_PATH = join(DATA_PATH, 'appdevice.json')
    DEFAULT_CASE_EXPORT_PATH = join(DATA_PATH, 'cases.json')
    BASIC_APP_API = join('.', 'tests', 'schemas', 'basic_app_api.yaml')
    CACHE_PATH = join('.', 'tests', 'tmp', 'cache')
    CASE_DB_PATH = join('.', 'tests', 'tmp', 'events_test.db')
    DB_PATH = join('.', 'tests', 'tmp', 'walkoff_test.db')
    EXECUTION_DB_PATH = join('.', 'tests', 'tmp', 'execution_test.db')
    NUMBER_PROCESSES = 2
    CACHE = {'type': 'disk', 'directory': CACHE_PATH}
