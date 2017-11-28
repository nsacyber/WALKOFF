import importlib
import json
import logging
import sys
from os import listdir
from os.path import isfile, join, splitext

import yaml

import core.config.paths
from core.config.paths import keywords_path

__logger = logging.getLogger(__name__)


def load_config():
    """ Loads Walkoff configuration from JSON file
    """
    global https
    self = sys.modules[__name__]
    if isfile(core.config.paths.config_path):
        try:
            with open(core.config.paths.config_path) as config_file:
                config = json.loads(config_file.read())
                for key, value in config.items():
                    if value:
                        if hasattr(core.config.paths, key):
                            setattr(core.config.paths, key, value)
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
        if hasattr(core.config.paths, key):
            output[key] = getattr(core.config.paths, key)
        elif hasattr(self, key):
            output[key] = getattr(self, key)

    with open(core.config.paths.config_path, 'w') as config_file:
        config_file.write(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': ')))


reinitialize_case_db_on_startup = True

tls_version = "1.2"
https = False

debug = True
default_server = True
host = "127.0.0.1"
port = 5000

walkoff_db_type = 'sqlite'
case_db_type = 'sqlite'
device_db_type = 'sqlite'
secret_key = 'SHORTSTOPKEYTEST'
walkoff_version = '0.5.0'

# Loads the keywords into the environment filter for use
JINJA_GLOBALS = {splitext(fn)[0]: getattr(importlib.import_module("core.keywords." + splitext(fn)[0]), "main")
                 for fn in listdir(keywords_path) if
                 isfile(join(keywords_path, fn)) and not splitext(fn)[0] in ["__init__", "."]}

num_processes = 5

# Function Dict Paths/Initialization

app_apis = {}


def load_app_apis(apps_path=None):
    from core.helpers import list_apps, format_exception_message
    global app_apis
    if apps_path is None:
        apps_path = core.config.paths.apps_path
    try:
        with open(join(core.config.paths.walkoff_schema_path), 'r') as schema_file:
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
                    from core.validator import validate_app_spec
                    validate_app_spec(api, app)
                    app_apis[app] = api
            except Exception as e:
                __logger.error(
                    'Cannot load apps api for app {0}: Error {1}'.format(app, str(format_exception_message(e))))


def initialize():
    load_config()
    from apps import cache_apps
    cache_apps(core.config.paths.apps_path)
    load_app_apis()
