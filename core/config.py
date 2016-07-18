import json, os
import playbook as pb
import core.logging as logging
from pkg_resources import WorkingSet , DistributionNotFound

path = "data/walkoff.config"
backupPath = "data/backup/walkoff_backup.config"
defaultPath = "data/backup/walkoff_default.config"
config = None

#Gets all the app instances
def getApps(path="apps"):
    apps = next(os.walk(path))[1]
    return apps

def getAppManifest(app):
    path = "apps/" + app + "/app.manifest"
    try:
        manifest = json.loads(open(path, "r").read())
        return manifest
    except Exception as e:
        return None

#Checks to ensure app dependencies are installed; installs dependency if doesnt exist
def checkApps(apps=[]):
    working_set = WorkingSet()
    for app in apps:
        manifest = getAppManifest(app)
        if manifest:
            for dependency in  manifest["externalDependencies"]:
                try:
                    dep = working_set.require(dependency)
                except DistributionNotFound:
                    from setuptools.command.easy_install import main as install
                    try:
                        install([dependency])
                    except Exception as e:
                        print e


def displayConfig(section):
    if config != None:
        if section in config:
            return config[section]
    else:
        return {"status": "Could not display Config"}

def editKeyValue(section, key, value=None):
    if section in config:
        if key in config[section]:
            config[section][key] = value
            return {"status" : "Edited config"}
    return {"status": "Could not edit config"}

def addKeyValue(section, key, value=None):
    if section in config:
        if key not in config[section]:
            config[section][key] = value
            return {"status" : "added config parameter"}
        else:
            return {"status" : "Could not add new parameter"}
    return {"status": "Could not add config parameter"}

def removeConfigKey(section, key):
    if section in config:
        if key in config[section]:
            print len(config[section])
            del config[section][key]
            print len(config[section])
            return {"status" : "play removed"}
    return {"status" : "could not remove play"}

def savePlaybookToFile():
    try:
        backup = playbook
        with open(globalConfig["playbookPath"], "w") as f:
            text = playbook.generatePlaybook()
            pp = json.dumps(text, sort_keys=True, indent=4, separators=(',', ': '))
            f.write(pp)


        return {"status" : "saved playbook"}
    except Exception as e:
        with open(globalConfig["playbookPath"], "w") as f:
            f.write(backup)

        return {"status" : "could not save playbook", "error" : e.message}

def refreshPlaybook():
    global playbook
    playbook = pb.Playbook(globalConfig["playbookPath"])

def saveConfig():
    try:
        backup = config
        with open(path, "w") as f:
            f.write(json.dumps(config, sort_keys=True, indent=4, separators=(',', ':')))

        return {"status" : "saved config"}
    except Exception as e:
        with open(path, "w") as f:
            f.write(json.dumps(backup, sort_keys=True, indent=4, separators=(',', ':')))
        return {"status" : "could not save config", "error" : e.message}

def refreshConfig():
    global config, executionConfig, loggingConfig, interfaceConfig, globalConfig, appConfig, authConfig
    config = json.load(open(path, "r"))
    executionConfig = config["execution"]
    loggingConfig = config["logging"]
    interfaceConfig = config["interface"]
    globalConfig = config["global"]
    authConfig = config["auth"]

def revert():
    try:

        with open(backupPath, "r") as backupFile:
           open(path, "w").write(backupFile.read())
        return {"status" : "reverted configuration file to baseline"}
    except Exception as e:
        return {"status" : "could not revert configuration file", "error":e.message}

def gotoDefaultConfig():
    global executionConfig, loggingConfig, interfaceConfig, globalConfig, authConfig, defaultConfig
    with open(defaultPath, "r") as f:
        defaultConfig = json.load(f)
        executionConfig = defaultConfig["execution"]
        loggingConfig = defaultConfig["logging"]
        interfaceConfig = defaultConfig["interface"]
        globalConfig = defaultConfig["global"]
        authConfig = defaultConfig["auth"]

authConfig = None
globalConfig = None
interfaceConfig = None
loggingConfig = None
executionConfig = None
defaultConfig = None
config = None

try:
    with open(path, "r") as f:
        config = json.load(f)
        executionConfig = config["execution"]
        loggingConfig = config["logging"]
        interfaceConfig = config["interface"]
        globalConfig = config["global"]
        authConfig = config["auth"]

except Exception as e:
    msg =  {"status" : "Could not load config using default configuration", "error" : e.message}
    logging.logger.log.send(message=msg)
    with open(backupPath, "r") as f:
        defaultConfig = json.load(f)
        executionConfig = defaultConfig["execution"]
        loggingConfig = defaultConfig["logging"]
        interfaceConfig = defaultConfig["interface"]
        globalConfig = defaultConfig["global"]
        authConfig = defaultConfig["auth"]
    print e.args


playbook = pb.Playbook(globalConfig["playbookPath"])