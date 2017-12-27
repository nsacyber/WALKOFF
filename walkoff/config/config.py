import importlib
import json
import logging
import sys
from os import listdir
from os.path import isfile, join, splitext

import yaml

import walkoff.config.paths
from walkoff.config.paths import keywords_path

__logger = logging.getLogger(__name__)


def load_config():
    """ Loads Walkoff configuration from JSON file
    """
    self = sys.modules[__name__]
    if isfile(walkoff.config.paths.config_path):
        try:
            with open(walkoff.config.paths.config_path) as config_file:
                config = json.loads(config_file.read())
                for key, value in config.items():
                    if value:
                        if hasattr(walkoff.config.paths, key):
                            setattr(walkoff.config.paths, key, value)
                        elif hasattr(self, key):
                            setattr(self, key, value)
        except (IOError, OSError, ValueError):
            __logger.warning('Could not read config file.', exc_info=True)


def write_values_to_file(keys=None):
    """ Writes the current walkoff configuration to a file
    """
    if keys is None:
        keys = ['apps_path', 'workflows_path', 'templates_path', 'db_path', 'case_db_path', 'certificate_path',
                'private_key_path', 'default_appdevice_export_path', 'default_case_export_path', 'keywords_path',
                'logging_config_path', 'notifications', 'reinitialize_case_db_on_startup', 'tls_version', 'https',
                'host', 'port', 'walkoff_db_type', 'case_db_type', 'num_threads', 'debug', 'default_server']
    self = sys.modules[__name__]

    output = {}
    for key in keys:
        if hasattr(walkoff.config.paths, key):
            output[key] = getattr(walkoff.config.paths, key)
        elif hasattr(self, key):
            output[key] = getattr(self, key)

    with open(walkoff.config.paths.config_path, 'w') as config_file:
        config_file.write(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': ')))


reinitialize_case_db_on_startup = True

host = "127.0.0.1"
port = 5000

zmq_requests_address = 'tcp://127.0.0.1:5555'
zmq_results_address = 'tcp://127.0.0.1:5556'
zmq_communication_address = 'tcp://127.0.0.1:5557'

walkoff_db_type = 'sqlite'
case_db_type = 'sqlite'
device_db_type = 'sqlite'
secret_key = 'SHORTSTOPKEYTEST'
walkoff_version = '0.5.0'

# Loads the keywords into the environment filter for use
JINJA_GLOBALS = {splitext(fn)[0]: getattr(importlib.import_module("walkoff.keywords." + splitext(fn)[0]), "main")
                 for fn in listdir(keywords_path) if
                 isfile(join(keywords_path, fn)) and not splitext(fn)[0] in ["__init__", "."]}

num_processes = 5

# Function Dict Paths/Initialization

app_apis = {}


def load_app_apis(apps_path=None):
    from walkoff.core.helpers import list_apps, format_exception_message
    global app_apis
    if apps_path is None:
        apps_path = walkoff.config.paths.apps_path
    try:
        with open(join(walkoff.config.paths.walkoff_schema_path), 'r') as schema_file:
            json.loads(schema_file.read())
    except Exception as e:
        __logger.fatal('Could not load JSON schema for apps. Shutting down...: ' + str(e))
        sys.exit(1)
    else:
        for app in list_apps(apps_path):
            try:
                url = join(apps_path, app, 'api.yaml')
                with open(url) as function_file:
                    api = yaml.load(function_file.read())
                    from walkoff.core.validator import validate_app_spec
                    validate_app_spec(api, app)
                    app_apis[app] = api
            except Exception as e:
                __logger.error(
                    'Cannot load apps api for app {0}: Error {1}'.format(app, str(format_exception_message(e))))


def initialize():
    load_config()
    from apps import cache_apps
    cache_apps(walkoff.config.paths.apps_path)
    load_app_apis()
