from os.path import join

data_path = join('.', 'data')

api_path = join('.', 'walkoff', 'api')
apps_path = join('.', 'apps')
case_db_path = join(data_path, 'events.db')

client_path = join('.', 'walkoff', 'client')
config_path = join(data_path, 'walkoff.config')
db_path = join(data_path, 'walkoff.db')
default_appdevice_export_path = join(data_path, 'appdevice.json')
default_case_export_path = join(data_path, 'cases.json')
device_db_path = join(data_path, 'devices.db')
interfaces_path = join('.', 'interfaces')
keywords_path = join('.', 'walkoff', 'keywords')
logging_config_path = join(data_path, 'log', 'logging.json')

walkoff_schema_path = join(data_path, 'walkoff_schema.json')
workflows_path = join('.', 'workflows')

keys_path = join('.', '.certificates')
certificate_path = join(keys_path, 'walkoff.crt')
private_key_path = join(keys_path, 'walkoff.key')
zmq_private_keys_path = join(keys_path, 'private_keys')
zmq_public_keys_path = join(keys_path, 'public_keys')
