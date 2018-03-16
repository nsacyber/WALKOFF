import json
import logging
import sys
from os.path import isfile, join, abspath

import yaml

import walkoff.config.paths

logger = logging.getLogger(__name__)


def write_values_to_file(keys=None):
    """ Writes the current walkoff configuration to a file
    """
    if keys is None:
        keys = ['apps_path', 'workflows_path', 'db_path', 'case_db_path', 'certificate_path',
                'private_key_path', 'default_appdevice_export_path', 'default_case_export_path',
                'logging_config_path', 'notifications', 'REINITIALIZE_CASE_DB_ON_STARTUP',
                'HOST', 'PORT', 'ZMQ_RESULTS_ADDRESS', 'ZMQ_COMMUNICATION_ADDRESS',  'NUMBER_PROCESSES',
                'NUM_THREADS_PER_PROCESS', 'WALKOFF_DB_TYPE', 'CASE_DB_TYPE', 'EXECUTION_DB_TYPE', 'CACHE_CONFIG']

    output = {}
    for key in keys:
        if hasattr(walkoff.config.paths, key):
            output[key] = getattr(walkoff.config.paths, key)
        elif hasattr(Config, key):
            output[key] = getattr(Config, key)

    with open(walkoff.config.paths.config_path, 'w') as config_file:
        config_file.write(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': ')))


# Function Dict Paths/Initialization

app_apis = {}


def load_app_apis(apps_path=None):
    """Loads App APIs
    
    Args:
        apps_path (str, optional): Optional path to specifiy for the apps. Defaults to None, but will be set to the
            apps_path variable in walkoff.config.paths
    """
    from walkoff.helpers import list_apps, format_exception_message
    global app_apis
    if apps_path is None:
        apps_path = walkoff.config.paths.apps_path
    try:
        with open(join(walkoff.config.paths.walkoff_schema_path), 'r') as schema_file:
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
                    validate_app_spec(api, app, walkoff.config.paths.walkoff_schema_path)
                    app_apis[app] = api
            except Exception as e:
                logger.error(
                    'Cannot load apps api for app {0}: Error {1}'.format(app, str(format_exception_message(e))))


class Config(object):
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

    @classmethod
    def load_config(cls):
        """ Loads Walkoff configuration from JSON file
        """
        if isfile(walkoff.config.paths.config_path):
            try:
                with open(walkoff.config.paths.config_path) as config_file:
                    config = json.loads(config_file.read())
                    for key, value in config.items():
                        if value:
                            if key == 'cache':
                                cls.CACHE_CONFIG = value
                            elif hasattr(walkoff.config.paths, key):
                                setattr(walkoff.config.paths, key, value)
                            elif hasattr(cls, key):
                                setattr(cls, key, value)
            except (IOError, OSError, ValueError):
                logger.warning('Could not read config file.', exc_info=True)


class AppConfig(object):
    # CHANGE SECRET KEY AND SECURITY PASSWORD SALT!!!

    SECRET_KEY = 'SHORTSTOPKEYTEST'
    SQLALCHEMY_DATABASE_URI = '{0}://{1}'.format(Config.WALKOFF_DB_TYPE, abspath(
        walkoff.config.paths.db_path)) if Config.WALKOFF_DB_TYPE != 'sqlite' else '{0}:///{1}'.format(
        Config.WALKOFF_DB_TYPE, abspath(walkoff.config.paths.db_path))
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
    cache_apps(walkoff.config.paths.apps_path)
    load_app_apis()
