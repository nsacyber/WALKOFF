from os import sep
from os.path import join

test_path = join('.', 'tests')
test_workflows_path = join('.', 'tests', 'testWorkflows') + sep
test_workflows_path_with_generated = join('.', 'tests', 'testWorkflows', 'testGeneratedWorkflows') + sep
test_workflows_backup_path = join('.', 'tests', 'testWorkflows', 'testGeneratedWorkflows_bkup') + sep
test_apps_path = join('.', 'tests', 'apps')
test_data_dir_name = 'testdata'
test_data_path = join('.', 'tests', test_data_dir_name)
test_appdevice_backup = join(test_data_path, 'appdevice.json')
