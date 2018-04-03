import json
import logging
import logging.config
import sys
from os.path import isfile, join, abspath, sep
import warnings

import yaml

logger = logging.getLogger(__name__)

app_apis = {}

walkoff_external = abspath(r"C:\Users\589941\PycharmProjects\PipVersion3\NEWPIP_Walkoff\walkoff_external")
walkoff_internal = abspath(__file__).rsplit(sep, 1)[0]


def load_app_apis(apps_path=None):
    """Loads App APIs
    
    Args:
        apps_path (str, optional): Optional path to specify for the apps. Defaults to None, but will be set to the
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


def setup_logger():
    log_config = None
    if isfile(Config.LOGGING_CONFIG_PATH):
        try:
            with open(Config.LOGGING_CONFIG_PATH, 'rt') as log_config_file:
                log_config = json.loads(log_config_file.read())
        except (IOError, OSError):
            print('Could not read logging JSON file {}'.format(Config.LOGGING_CONFIG_PATH))
        except ValueError:
            print('Invalid JSON in logging config file')
    else:
        print('No logging config found')

    if log_config is not None:
        logging.config.dictConfig(log_config)
    else:
        logging.basicConfig()
        logger.info("Basic logging is being used")

    def send_warnings_to_log(message, category, filename, lineno, file=None):
        logging.warning(
            '%s:%s: %s:%s' %
            (filename, lineno, category.__name__, message))
        return

    warnings.showwarning = send_warnings_to_log


class Config(object):
    # CONFIG VALUES

    CLEAR_CASE_DB_ON_STARTUP = True

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
    NUMBER_THREADS_PER_PROCESS = 3

    # Database types
    WALKOFF_DB_TYPE = 'sqlite'
    CASE_DB_TYPE = 'sqlite'
    EXECUTION_DB_TYPE = 'sqlite'

    # PATHS
    # ROOT_PATH = abspath('.')
    WALKOFF_INTERNAL_PATH = walkoff_internal
    WALKOFF_EXTERNAL_PATH = walkoff_external

    DATA_PATH = join(WALKOFF_EXTERNAL_PATH, 'data')
    API_PATH = join(WALKOFF_INTERNAL_PATH, 'api')
    APPS_PATH = join(WALKOFF_EXTERNAL_PATH, 'apps')
    APPBASE_PATH = join(WALKOFF_INTERNAL_PATH, 'appbase')
    CACHE_PATH = join(DATA_PATH, 'cache')
    CASE_DB_PATH = join(DATA_PATH, 'events.db')
    CACHE = {"type": "disk", "directory": CACHE_PATH, "shards": 8, "timeout": 0.01, "retry": True}
    TEMPLATES_PATH = join(WALKOFF_INTERNAL_PATH, 'templates')

    CLIENT_PATH = join(WALKOFF_INTERNAL_PATH, 'client')
    CONFIG_PATH = join(DATA_PATH, 'walkoff.config')
    DB_PATH = join(DATA_PATH, 'walkoff.db')
    DEFAULT_APPDEVICE_EXPORT_PATH = join(DATA_PATH, 'appdevice.json')
    DEFAULT_CASE_EXPORT_PATH = join(DATA_PATH, 'cases.json')
    EXECUTION_DB_PATH = join(DATA_PATH, 'execution.db')
    INTERFACES_PATH = join(WALKOFF_EXTERNAL_PATH, 'interfaces')
    INTERFACEBASE_PATH = join(WALKOFF_INTERNAL_PATH, 'interfacebase')
    LOGGING_CONFIG_PATH = join(DATA_PATH, 'log', 'logging.json')

    WALKOFF_SCHEMA_PATH = join(DATA_PATH, 'walkoff_schema.json')
    # WORKFLOWS_PATH = join('.', 'workflows')

    KEYS_PATH = join(WALKOFF_EXTERNAL_PATH, '.certificates')
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
                            if hasattr(cls, key.upper()):
                                setattr(cls, key.upper(), value)
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
                output[key.lower()] = getattr(cls, key.upper())

        with open(cls.CONFIG_PATH, 'w') as config_file:
            config_file.write(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': ')))


class AppConfig(object):
    # CHANGE SECRET KEY AND SECURITY PASSWORD SALT!!!

    SECRET_KEY = 'SHORTSTOPKEYTEST'
    SQLALCHEMY_DATABASE_URI = '{0}://{1}'.format(Config.WALKOFF_DB_TYPE, abspath(
        Config.DB_PATH)) if Config.WALKOFF_DB_TYPE != 'sqlite' else '{0}:///{1}'.format(Config.WALKOFF_DB_TYPE,
                                                                                        abspath(Config.DB_PATH))

    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['refresh']
    JWT_TOKEN_LOCATION = 'headers'


def initialize():
    """Loads the config file, loads the app cache, and loads the app APIs into memory
    """
    setup_logger()
    Config.load_config()
    from walkoff.appgateway import cache_apps
    sys.path.insert(0, abspath(Config.WALKOFF_EXTERNAL_PATH))
    print("calling installed apps path")
    cache_apps(Config.APPS_PATH, relative=False)
    print("calling appbase")
    cache_apps("walkoff.appbase", relative=False)
    load_app_apis()
