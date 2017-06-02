import importlib
import json
import sys
import logging
from os import listdir, environ, pathsep
from os.path import isfile, join, splitext
import core.config.paths
from core.helpers import list_apps
from core.config.paths import keywords_path, graphviz_path
from collections import OrderedDict
import yaml
import jsonschema

__logger = logging.getLogger(__name__)


def load_config():
    """ Loads Walkoff configuration from JSON file
    """
    global https
    self = sys.modules[__name__]
    with open(core.config.paths.config_path) as config_file:
        config = json.loads(config_file.read())
        for key, value in config.items():
            if value:
                if hasattr(core.config.paths, key):
                    setattr(core.config.paths, key, value)
                elif hasattr(self, key):
                    setattr(self, key, value)


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


# Enables/Disables Browser Notifications
notifications = "True"

# Path to graphviz location
environ["PATH"] += (pathsep + graphviz_path)

# Database Path

reinitialize_case_db_on_startup = True

tls_version = "1.2"
https = "false"

debug = "True"
default_server = "True"
host = "127.0.0.1"
port = "5000"

walkoff_db_type = 'sqlite'
case_db_type = 'sqlite'

# Loads the keywords into the environment filter for use
JINJA_GLOBALS = {splitext(fn)[0]: getattr(importlib.import_module("core.keywords." + splitext(fn)[0]), "main")
                 for fn in listdir(keywords_path) if
                 isfile(join(keywords_path, fn)) and not splitext(fn)[0] in ["__init__", "."]}

# Active Execution (Workflows called from constant loop) settings.
# secondsDelay - delay in seconds between execution loops
# maxJobs - maximum number of jobs to be run at once
execution_settings = {
    "secondsDelay": 0.1,
    "maxJobs": 2
}

num_threads = 5
threadpool_shutdown_timeout_sec = 3

# Function Dict Paths/Initialization

function_info = None


def load_function_info():
    """ Loads the app action metadata
    """
    global function_info
    with open(core.config.paths.function_info_path) as f:
        function_info = json.loads(f.read())
    app_funcs = {}
    for app in list_apps():
        try:
            with open(join(core.config.paths.apps_path, app, 'functions.json')) as function_file:
                app_funcs[app] = json.loads(function_file.read())
        except Exception as e:
            __logger.error('Cannot load function metadata: Error {0}'.format(e))
    function_info['apps'] = app_funcs

app_apis = {}


def load_app_apis():
    global app_apis
    try:
        with open(join(core.config.paths.schema_path, 'new_schema.json'), 'r') as schema_file:
            schema = json.loads(schema_file.read())
    except Exception as e:
        print('Could not load JSON schema for apps. Shutting down...: ' + str(e))
        sys.exit(1)
    else:
        for app in list_apps():
            try:
                url = join(core.config.paths.apps_path, app, 'api.yaml')
                with open(url) as function_file:
                    api = yaml.load(function_file.read())
                    jsonschema.validate(api, schema)
                    from core.validator import validate_spec
                    validate_spec(api)
                    app_apis[app] = api
            except Exception as e:
                print('Cannot load apps api: Error {0}'.format(e))
    print(app_apis)
load_config()

load_app_apis()

try:
    with open(core.config.paths.events_path) as f:
        possible_events = json.loads(f.read(), object_pairs_hook=OrderedDict)
        possible_events = [{'type': element_type, 'events': events} for element_type, events in possible_events.items()]
except (IOError, OSError) as e:
    __logger.error('Cannot load events metadata. Returning empty list. Error: {0}'.format(e))
    possible_events = []

load_function_info()
