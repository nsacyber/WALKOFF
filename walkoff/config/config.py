import json
import logging
import sys
from os.path import isfile, join, abspath

import yaml

logger = logging.getLogger(__name__)

app_apis = {}


def load_app_apis(apps_path=None):
    """Loads App APIs
    
    Args:
        apps_path (str, optional): Optional path to specifiy for the apps. Defaults to None, but will be set to the
            apps_path variable in Config object
    """
    from walkoff.helpers import list_apps, format_exception_message
    global app_apis
    if apps_path is None:
        apps_path = Config.APPS_PATH
    try:
        with open(join(Config.WALKOFF_SCHEMA_PATH), 'r') as schema_file:
            json.loads(schema_file.read())
    except Exception as e:
        logger.fatal('Could not load JSON schema for apps. Shutting down...: ' + str(e))
        sys.exit(1)
    else:
        for app in list_apps(apps_path):
            try:
                url = join(apps_path, app, 'api.yaml')
                with open(url) as function_file:
                    api = yaml.load(function_file.read())
                    from walkoff.appgateway.validator import validate_app_spec
                    validate_app_spec(api, app, Config.WALKOFF_SCHEMA_PATH)
                    app_apis[app] = api
            except Exception as e:
                logger.error(
                    'Cannot load apps api for app {0}: Error {1}'.format(app, str(format_exception_message(e))))


class Config(object):
    # CONFIG VALUES

    REINITIALIZE_CASE_DB_ON_STARTUP = True

    # IP and port for the webserver
    HOST = "127.0.0.1"
    PORT = 5000

    # IP addresses and ports for IPC (inter-process communication). Do not change these unless necessary. There must
    # not be conflicts.
    ZMQ_RESULTS_ADDRESS = 'tcp://127.0.0.1:5556'
    ZMQ_COMMUNICATION_ADDRESS = 'tcp://127.0.0.1:5557'

    # Specify the number of worker processes, and the number of threads for each worker process. Multiplying these
    # numbers together specifies the max number of workflows that may be executing at the same time.
    NUMBER_PROCESSES = 4
    NUM_THREADS_PER_PROCESS = 3

    # Database types
    WALKOFF_DB_TYPE = 'sqlite'
    CASE_DB_TYPE = 'sqlite'
    EXECUTION_DB_TYPE = 'sqlite'

    CACHE_CONFIG = None

    # PATHS

    DATA_PATH = join('.', 'data')

    API_PATH = join('.', 'walkoff', 'api')
    APPS_PATH = join('.', 'apps')
    CACHE_PATH = join('.', 'data', 'cache')
    CASE_DB_PATH = join(DATA_PATH, 'events.db')

    CLIENT_PATH = join('.', 'walkoff', 'client')
    CONFIG_PATH = join(DATA_PATH, 'walkoff.config')
    DB_PATH = join(DATA_PATH, 'walkoff.db')
    DEFAULT_APPDEVICE_EXPORT_PATH = join(DATA_PATH, 'appdevice.json')
    DEFAULT_CASE_EXPORT_PATH = join(DATA_PATH, 'cases.json')
    EXECUTION_DB_PATH = join(DATA_PATH, 'execution.db')
    INTERFACES_PATH = join('.', 'interfaces')
    LOGGING_CONFIG_PATH = join(DATA_PATH, 'log', 'logging.json')

    WALKOFF_SCHEMA_PATH = join(DATA_PATH, 'walkoff_schema.json')
    WORKFLOWS_PATH = join('.', 'workflows')

    KEYS_PATH = join('.', '.certificates')
    CERTIFICATE_PATH = join(KEYS_PATH, 'walkoff.crt')
    PRIVATE_KEY_PATH = join(KEYS_PATH, 'walkoff.key')
    ZMQ_PRIVATE_KEYS_PATH = join(KEYS_PATH, 'private_keys')
    ZMQ_PUBLIC_KEYS_PATH = join(KEYS_PATH, 'public_keys')

    @classmethod
    def load_config(cls):
        """ Loads Walkoff configuration from JSON file
        """
        if isfile(cls.CONFIG_PATH):
            try:
                with open(cls.CONFIG_PATH) as config_file:
                    config = json.loads(config_file.read())
                    for key, value in config.items():
                        if value:
                            if key == 'cache':
                                cls.CACHE_CONFIG = value
                            if hasattr(cls, key):
                                setattr(cls, key, value)
            except (IOError, OSError, ValueError):
                logger.warning('Could not read config file.', exc_info=True)

    @classmethod
    def write_values_to_file(cls, keys=None):
        """ Writes the current walkoff configuration to a file
        """
        if keys is None:
            keys = [key for key in dir(cls) if not key.startswith('__')]

        output = {}
        for key in keys:
            if hasattr(cls, key.upper()):
                output[key] = getattr(cls, key)

        with open(cls.CONFIG_PATH, 'w') as config_file:
            config_file.write(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': ')))


class AppConfig(object):
    # CHANGE SECRET KEY AND SECURITY PASSWORD SALT!!!

    SECRET_KEY = 'SHORTSTOPKEYTEST'
    SQLALCHEMY_DATABASE_URI = '{0}://{1}'.format(Config.WALKOFF_DB_TYPE, abspath(
        Config.DB_PATH)) if Config.WALKOFF_DB_TYPE != 'sqlite' else '{0}:///{1}'.format(Config.WALKOFF_DB_TYPE,
                                                                                        abspath(Config.DB_PATH))
    SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'
    SECURITY_TRACKABLE = False
    SECURITY_PASSWORD_SALT = 'something_super_secret_change_in_production'
    SECURITY_POST_LOGIN_VIEW = '/'
    WTF_CSRF_ENABLED = False
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['refresh']
    JWT_TOKEN_LOCATION = 'headers'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


def initialize():
    """Loads the config file, loads the app cache, and loads the app APIs into memory
    """
    Config.load_config()
    from walkoff.appgateway import cache_apps
    cache_apps(Config.APPS_PATH)
    load_app_apis()
