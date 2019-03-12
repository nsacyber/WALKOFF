import json
import logging
import logging.config
import os
import sys
import warnings
from os.path import isfile, join, abspath

import yaml

from api_gateway.helpers import format_db_path

logger = logging.getLogger(__name__)


def load_app_apis():
    """Loads App APIs

    Args:
        apps_path (str, optional): Optional path to specify for the apps. Defaults to None, but will be set to the
            apps_path variable in Config object
    """

    from api_gateway.helpers import list_apps, format_exception_message
    global app_apis
    try:
        with open(join(Config.WALKOFF_SCHEMA_PATH), 'r') as schema_file:
            json.loads(schema_file.read())
    except Exception as e:
        logger.fatal('Could not load JSON schema for apps. Shutting down...: ' + str(e))
        sys.exit(1)
    else:
        for app, api in _cache.items():
            try:
                api = yaml.load(function_file.read())
                from api_gateway.appgateway.validator import validate_app_spec
                validate_app_spec(api, app, Config.WALKOFF_SCHEMA_PATH)
                app_apis[app] = api
            except Exception as e:
                logger.error(
                    f'Cannot load apps api for app {app}: Error {str(format_exception_message(e))}')


def setup_logger():
    log_config = None
    logging.basicConfig()
    if isfile(Config.LOGGING_CONFIG_PATH):
        try:
            with open(Config.LOGGING_CONFIG_PATH, 'r') as log_config_file:
                log_config = json.loads(log_config_file.read())
        except (IOError, OSError):
            logger.info(f"Could not read logging config file: {Config.LOGGING_CONFIG_PATH}")
        except ValueError:
            logger.info(f"Invalid JSON in logging config file: {Config.LOGGING_CONFIG_PATH}")
    else:
        logger.info(f"Could not find logging config file: {Config.LOGGING_CONFIG_PATH}")

    if log_config is not None:
        logging.config.dictConfig(log_config)
    else:
        logger.info("Using basic logging config.")

    def send_warnings_to_log(message, category, filename, lineno, file=None, *args):
        logging.warning(
            '%s:%s: %s:%s' %
            (filename, lineno, category.__name__, message))
        return

    warnings.showwarning = send_warnings_to_log


class Config(object):
    from common.config import config as common_config
    # TODO: Merge triple-play config with this old config and replace the hack below
    common_config = common_config
    # CONFIG VALUES

    # IP and port for the webserver
    IP = "127.0.0.1"
    PORT = 5000

    # IP addresses and ports for IPC (inter-process communication). Do not change these unless necessary. There must
    # not be conflicts.
    ZMQ_RESULTS_ADDRESS = 'tcp://127.0.0.1:5556'
    ZMQ_COMMUNICATION_ADDRESS = 'tcp://127.0.0.1:5557'

    # Specify the number of worker processes, and the number of threads for each worker process. Multiplying these
    # numbers together specifies the max number of workflows that may be executing at the same time.
    NUMBER_PROCESSES = 4
    NUMBER_THREADS_PER_PROCESS = 3

    # Database types
    WALKOFF_DB_TYPE = 'sqlite'
    EXECUTION_DB_TYPE = 'sqlite'

    WALKOFF_DB_HOST = 'localhost'
    EXECUTION_DB_HOST = 'localhost'

    # PATHS
    DATA_PATH = 'data'

    API_PATH = join("api_gateway", "api")
    CACHE = {'type': 'redis', 'host': 'localhost', 'port': 6379}

    CLIENT_PATH = join("api_gateway", "client")
    CONFIG_PATH = join(DATA_PATH, 'api_gateway.config')
    DB_PATH = abspath(join(DATA_PATH, 'api_gateway.db'))
    DEFAULT_APPDEVICE_EXPORT_PATH = join(DATA_PATH, 'appdevice.json')
    EXECUTION_DB_PATH = abspath(join(DATA_PATH, 'execution.db'))

    LOGGING_CONFIG_PATH = join(DATA_PATH, 'log', 'logging.json')

    WALKOFF_SCHEMA_PATH = join(DATA_PATH, 'walkoff_schema.json')
    WORKFLOWS_PATH = join(DATA_PATH, 'workflows')

    KEYS_PATH = join("api_gateway", '.certificates')
    CERTIFICATE_PATH = join(KEYS_PATH, 'api_gateway.crt')
    PRIVATE_KEY_PATH = join(KEYS_PATH, 'api_gateway.key')

    # AppConfig
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = format_db_path(WALKOFF_DB_TYPE, DB_PATH, 'WALKOFF_DB_USERNAME', 'WALKOFF_DB_PASSWORD',
                                             WALKOFF_DB_HOST)

    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['refresh']
    JWT_TOKEN_LOCATION = 'headers'

    JWT_BLACKLIST_PRUNE_FREQUENCY = 1000
    MAX_STREAM_RESULTS_SIZE_KB = 156

    SEPARATE_WORKERS = False
    SEPARATE_RECEIVER = False
    SEPARATE_INTERFACES = False
    ITEMS_PER_PAGE = 20
    ACTION_EXECUTION_STRATEGY = 'local'

    EXECUTION_DB_USERNAME = ''
    EXECUTION_DB_PASSWORD = ''

    WALKOFF_DB_USERNAME = ''
    WALKOFF_DB_PASSWORD = ''

    SERVER_PUBLIC_KEY = ''
    SERVER_PRIVATE_KEY = ''
    CLIENT_PUBLIC_KEY = ''
    CLIENT_PRIVATE_KEY = ''
    ACCUMULATOR_TYPE = 'external'

    SECRET_KEY = "SHORTSTOPKEY"

    __passwords = ['EXECUTION_DB_PASSWORD', 'WALKOFF_DB_PASSWORD', 'SERVER_PRIVATE_KEY',
                   'CLIENT_PRIVATE_KEY', 'SERVER_PUBLIC_KEY', 'CLIENT_PUBLIC_KEY', 'SECRET_KEY']

    WORKFLOW_RESULTS_HANDLER = 'zmq'
    WORKFLOW_RESULTS_PROTOCOL = 'protobuf'
    WORKFLOW_RESULTS_KAFKA_CONFIG = {'bootstrap.servers': 'localhost:9092', 'group.id': 'results'}
    WORKFLOW_RESULTS_KAFKA_TOPIC = 'results'

    WORKFLOW_COMMUNICATION_HANDLER = 'zmq'
    WORKFLOW_COMMUNICATION_PROTOCOL = 'protobuf'
    WORKFLOW_COMMUNICATION_KAFKA_CONFIG = {'bootstrap.servers': 'localhost:9092', 'group.id': 'comm'}
    WORKFLOW_COMMUNICATION_KAFKA_TOPIC = 'comm'

    SEPARATE_PROMETHEUS = False

    ALEMBIC_CONFIG = join('.', 'alembic.ini')

    SWAGGER_URL = '/api/docs'

    @classmethod
    def load_config(cls, config_path=None):
        """ Loads Walkoff configuration from JSON file

        Args:
            config_path (str): Optional path to the config. Defaults to the CONFIG_PATH class variable.
        """
        if config_path:
            cls.CONFIG_PATH = config_path
        if cls.CONFIG_PATH:
            try:
                if isfile(cls.CONFIG_PATH):
                    with open(cls.CONFIG_PATH) as config_file:
                        config = json.loads(config_file.read())
                        for key, value in config.items():
                            if value:
                                setattr(cls, key.upper(), value)
                        logger.info(f"Config file loaded: {cls.CONFIG_PATH}.")
                else:
                    logger.info(f"Could not find config file: {cls.CONFIG_PATH}")
            except (IOError, OSError, ValueError):
                logger.warning(f"Could not read config file: {cls.CONFIG_PATH}", exc_info=True)

        cls.SQLALCHEMY_DATABASE_URI = format_db_path(cls.WALKOFF_DB_TYPE, cls.DB_PATH, 'WALKOFF_DB_USERNAME',
                                                     'WALKOFF_DB_PASSWORD', cls.WALKOFF_DB_HOST)

    @classmethod
    def write_values_to_file(cls, keys=None):
        """ Writes the current walkoff configuration to a file"""
        if keys is None:
            keys = [key for key in dir(cls) if not key.startswith('__')]

        output = {}
        for key in keys:
            if key.upper() not in cls.__passwords and hasattr(cls, key.upper()):
                output[key.lower()] = getattr(cls, key.upper())

        with open(cls.CONFIG_PATH, 'w') as config_file:
            config_file.write(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': ')))
            logger.info(f"Wrote config file to: {cls.CONFIG_PATH}")

    @classmethod
    def load_env_vars(cls):
        for field in (field for field in dir(cls) if field.isupper()):
            if field in os.environ:
                var_type = type(getattr(cls, field))
                var = os.environ.get(field)
                if var_type == dict:
                    setattr(cls, field, json.loads(var))
                else:
                    setattr(cls, field, var_type(var))
                logger.info((f"Using environment variable: "
                             f"{field} = {f'{var}' if field not in cls.__passwords else '<hidden>'}"))

        cls.SQLALCHEMY_DATABASE_URI = format_db_path(cls.WALKOFF_DB_TYPE, cls.DB_PATH, 'WALKOFF_DB_USERNAME',
                                                     'WALKOFF_DB_PASSWORD', cls.WALKOFF_DB_HOST)


# TODO: Figure out nice way of ensuring the order of operations for all of the flask app init stuff
Config.load_config()
Config.load_env_vars()
setup_logger()
