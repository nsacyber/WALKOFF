import os
from os.path import join, sep

if os.environ.get('PYTHON_UNITTEST'):
    env_config_file = 'tests/'
else:
    env_config_file = '.'

apps_path = join('.', 'apps')
workflows_path = join('.', 'data', 'workflows')
templates_path = join('.', 'data', 'templates')
profile_visualizations_path = join('.', 'tests', 'profileVisualizations') + sep
keywords_path = join('.', 'core', 'keywords')
graphviz_path = "C:/Program Files (x86)/Graphviz2.38/bin"
certificate_path = join('.', 'data', 'shortstop.public.pem')
private_key_path = join('.', 'data', 'shortstop.private.pem')
function_info_path = join('.', 'data', 'functions.json')
events_path = join('.', 'data', 'events.json')
default_appdevice_export_path = join('.', 'data', 'appdevice.json')
default_case_export_path = join('.', 'data', 'cases.json')
data_path = join('.', 'data')
logging_config_path = join('.', 'data', 'log', 'logging.json')
api_path = join('.', 'server', 'api')
walkoff_schema_path = join(data_path, 'walkoff_schema.json')
function_api_path = join(data_path, 'functions.yaml')
AES_key_path = join('.', 'data', 'aes_key.txt')

# ENV specific (Note: configs that write to files during unittesting)
config_path = join(env_config_file, 'data', 'walkoff.config')
db_path = join(env_config_file, 'data', 'walkoff.db')
case_db_path = join(env_config_file, 'data', 'events.db')
