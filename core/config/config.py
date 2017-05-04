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


def write_values_to_file(values=None):
    """ Writes the current walkoff configuration to a file
    """
    if values is None:
        values = ["graphviz_path", "templates_path", "profile_visualizations_path", "keywords_path", "db_path",
                  "tls_version",
                  "certificate_path", "https", "private_key_path", "debug", "default_server", "host", "port"]
    self = sys.modules[__name__]
    f = open(core.config.paths.config_path, "r")
    parsed = json.loads(f.read())
    f.close()
    for key in values:
        parsed[key] = getattr(self, key)

    with open(core.config.paths.config_path, "w") as f:
        json.dump(parsed, f)

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
    try:
        with open(core.config.paths.function_info_path) as f:
            function_info = json.loads(f.read())
        app_funcs = {}
        for app in list_apps():
            with open(join(core.config.paths.apps_path, app, 'functions.json')) as function_file:
                app_funcs[app] = json.loads(function_file.read())
        function_info['apps'] = app_funcs

    except Exception as e:
        logging.getLogger(__name__).error('Cannot load function metadata: Error {0}'.format(e))

load_config()
try:
    with open(core.config.paths.events_path) as f:
        possible_events = json.loads(f.read(), object_pairs_hook=OrderedDict)
except (IOError, OSError):
    logging.getLogger(__name__).error('Cannot load events metadata. Returning empty dict: Error {0}'.format(e))
    possible_events = {}


load_function_info()


# Function to set config value
def set(key, value):
    self = sys.modules[__name__]
    if hasattr(self, key):
        setattr(self, key, value)
        return True
    return False
