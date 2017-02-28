from os import listdir, walk
from os.path import join, isfile, splitext

#
# Act as an interface for objects to access other event specific variables that might be needed
#

class Context(object):
    def __init__(self):
        self.workflows = self.getWorkflowsFromFolder()
        self.apps = self.getApps()

    @staticmethod
    def getWorkflowsFromFolder(path=join(".", "data", "workflows")):
        workflows = [join(path, workflow) for workflow in listdir(path) if isfile(join(path, workflow)) and not splitext(workflow)[0] in ["__init__", "."]]
        print(workflows)
        return workflows

    # Returns list of apps
    # Gets all the app instances
    @staticmethod
    def getApps(path="apps"):
        apps = next(walk(path))[1]
        return apps

running_context = Context()