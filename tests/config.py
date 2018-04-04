from os import sep
from os.path import join, abspath


test_path = abspath(__file__).rsplit(sep, 1)[0]
test_workflows_path = join(test_path, 'testWorkflows') + sep
test_apps_path = join(test_path, 'testapps')
test_data_dir_name = 'testdata'
test_data_path = join(test_path, test_data_dir_name)
test_appdevice_backup = join(test_data_path, 'appdevice.json')
test_cases_backup = join(test_data_path, 'cases.json')
basic_app_api = join(test_path, 'schemas', 'basic_app_api.yaml')
cache_path = join(test_path, 'tmp', 'cache')
test_case_db_path = join(test_path, 'tmp', 'events_test.db')
test_db_path = join(test_path, 'tmp', 'walkoff_test.db')
test_execution_db_path = join(test_path, 'tmp', 'execution_test.db')
