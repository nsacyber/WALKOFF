from walkoff.config import Config
from walkoff.helpers import format_db_path
from os.path import join

REDIS_HOST = "redis-primary"
APP_HOST = "walkoff-app-internal"
# WORKER_HOST = "172.18.0.4"

Config.load_config("data/walkoff.config")
Config.CACHE = {
    "type": "redis",
    "host": REDIS_HOST,
    "port": 6379
}
Config.HOST = "0.0.0.0"
Config.PORT = 80
Config.ZMQ_RESULTS_ADDRESS = 'tcp://{}:5556'.format(APP_HOST)
Config.ZMQ_COMMUNICATION_ADDRESS = 'tcp://{}:5557'.format(APP_HOST)
Config.SEPARATE_WORKERS = True
Config.DB_PATH = join('postgres-walkoffdb', 'walkoff.db')
Config.CASE_DB_PATH = join('postgres-casedb', 'events.db')
Config.EXECUTION_DB_PATH = join('postgres-executiondb', 'execution.db')

Config.WALKOFF_DB_TYPE = 'postgresql'
Config.CASE_DB_TYPE = 'postgresql'
Config.EXECUTION_DB_TYPE = 'postgresql'

Config.KEYS_PATH = join('.', 'certs')
Config.CERTIFICATE_PATH = join(Config.KEYS_PATH, 'tls.crt')
Config.PRIVATE_KEY_PATH = join(Config.KEYS_PATH, 'tls.key')
Config.ZMQ_PRIVATE_KEYS_PATH = join(Config.KEYS_PATH, 'private_keys')
Config.ZMQ_PUBLIC_KEYS_PATH = join(Config.KEYS_PATH, 'public_keys')

Config.SQLALCHEMY_DATABASE_URI = format_db_path(Config.WALKOFF_DB_TYPE, Config.DB_PATH, 'WALKOFF_DB_USERNAME', 'WALKOFF_DB_PASSWORD')

Config.NUMBER_PROCESSES = 1

Config.write_values_to_file()
