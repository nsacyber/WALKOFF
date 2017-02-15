import json, importlib, sys
from os import listdir, walk, sep, environ, pathsep
from os.path import isfile, join, splitext

def loadConfig():
    self = sys.modules[__name__]
    with open("./data/walkoff.config") as f:
        config = json.loads(f.read())
        for key in config.keys():
            if hasattr(self, key):
                setattr(self, key, config[key])

def writeValuesToFile(values=["graphVizPath", "templatesPath", "profileVisualizationsPath", "keywordsPath", "dbPath", "TLS_version", "certificatePath", "https", "privateKeyPath", "debug", "defaultServer", "host", "port"]):
    self = sys.modules[__name__]
    f = open("./data/walkoff.config", "r")
    parsed = json.loads(f.read())
    f.close()
    for key in values:
        parsed[key] = getattr(self, key)

    with open("./data/walkoff.config", "w") as f:
        json.dump(parsed, f)

loadConfig()

#Enables/Disables Browser Notifications
notifications = "True"

#Path to graphviz location
graphVizPath = "C:/Program Files (x86)/Graphviz2.38/bin"
environ["PATH"] += (pathsep+graphVizPath)

# Folder path for new templates
templatesPath = join('.', 'data', 'templates')
profileVisualizationsPath = join('.', 'tests', 'profileVisualizations') + sep

# Keyword folder path
keywordsPath = join('.', 'core', 'keywords')

#Database Path
dbPath = "data/walkoff.db"

case_db_path = join('data', 'events.db')
reinitialize_case_db_on_startup = True

TLS_version = "1.2"
certificatePath = "data/auth/shortstop.public.pem"
https = "false"
privateKeyPath = "data/auth/shortstop.private.pem"

debug = "True"
defaultServer = "True"
host = "127.0.0.1"
port = "5000"

#Loads the keywords into the environment filter for use
#[jinja2.filters.FILTERS.update({splitext(fn)[0]:getattr(importlib.import_module("core.keywords." + splitext(fn)[0]), "main")}) for fn in listdir(keywordsPath) if isfile(join(keywordsPath, fn)) and not splitext(fn)[0] == "__init__"]
JINJA_GLOBALS = {splitext(fn)[0]:getattr(importlib.import_module("core.keywords." + splitext(fn)[0]), "main")
                 for fn in listdir(keywordsPath) if isfile(join(keywordsPath, fn)) and not splitext(fn)[0] in ["__init__", "."]}

# Active Execution (Workflows called from constant loop) settings.
# secondsDelay - delay in seconds between execution loops
# maxJobs - maximum number of jobs to be run at once
executionSettings = {
    "secondsDelay": 0.1,
    "maxJobs": 2
}

# Logging Verbosity
logSettings = {
    "executed": True,
    "next": True
}

# Function Dict Paths/Initialization
functionConfigPath = join('.', 'data', 'functions.json')
functionConfig = None

try:
    with open(functionConfigPath) as f:
        functionConfig = json.loads(f.read())

except Exception as e:
    print(e)

#Returns list of apps
#Gets all the app instances
def getApps(path="apps"):
    apps = next(walk(path))[1]
    return apps

#Function to set config value
def set(key, value):
    self = sys.modules[__name__]
    if hasattr(self, key):
        setattr(self, key, value)
        return True
    return False






