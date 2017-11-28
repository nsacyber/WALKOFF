from os.path import join

data_path = join('.', 'data')

api_path = join('.', 'server', 'api')
apps_path = join('.', 'apps')
case_db_path = join(data_path, 'events.db')
certificate_path = join(data_path, 'shortstop.public.pem')
client_path = join('.', 'client')
config_path = join(data_path, 'walkoff.config')
db_path = join(data_path, 'walkoff.db')
default_appdevice_export_path = join(data_path, 'appdevice.json')
default_case_export_path = join(data_path, 'cases.json')
device_db_path = join(data_path, 'devices.db')
interfaces_path = join('.', 'interfaces')
keywords_path = join('.', 'core', 'keywords')
logging_config_path = join(data_path, 'log', 'logging.json')
private_key_path = join(data_path, 'shortstop.private.pem')
walkoff_schema_path = join(data_path, 'walkoff_schema.json')
workflows_path = join('.', 'workflows')

zmq_keys_path = join('.', '.certificates')
zmq_private_keys_path = join(zmq_keys_path, 'private_keys')
zmq_public_keys_path = join(zmq_keys_path, 'public_keys')
