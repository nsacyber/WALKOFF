import json, importlib
from os import listdir
from os.path import isfile, join, splitext
import jinja2

#Folder path for new templates
templatesPath = "data/templates/"

#Keyword folder path
keywordsPath = "core/keywords"

#Loads the keywords into the environment filter for use
[jinja2.filters.FILTERS.update({splitext(fn)[0]:getattr(importlib.import_module("core.keywords." + splitext(fn)[0]), "main")}) for fn in listdir(keywordsPath) if isfile(join(keywordsPath, fn)) and not splitext(fn)[0] == "__init__"]

#Active Execution (Workflows called from constant loop) settings.
#secondsDelay - delay in seconds between execution loops
#maxJobs - maximum number of jobs to be run at once
executionSettings = {
    "secondsDelay" : 0.1,
    "maxJobs" : 2
}

#Logging Verbosity
logSettings = {
    "executed" : True,
    "next" : True
}

#Function Dict Paths/Initialization
functionConfigPath = "data/functions.json"
functionConfig = None

try:
    with open(functionConfigPath) as f:
        functionConfig = json.loads(f.read())

except Exception as e:
    print(e)