from os import sep
from os.path import join

test_path = join('.', 'tests')
test_workflows_path = join('.', 'tests', 'testWorkflows') + sep
test_apps_path = join('.', 'tests', 'testapps')
test_data_dir_name = 'testdata'
test_data_path = join('.', 'tests', test_data_dir_name)
test_appdevice_backup = join(test_data_path, 'appdevice.json')
test_cases_backup = join(test_data_path, 'cases.json')
basic_app_api = join('.', 'tests', 'schemas', 'basic_app_api.yaml')
cache_path = join('.', 'tests', 'tmp')
test_case_db_path = join('.', 'tests', 'tmp', 'events_test.db')
test_db_path = join('.', 'tests', 'tmp', 'walkoff_test.db')
test_execution_db_path = join('.', 'tests', 'tmp', 'execution_test.db')
