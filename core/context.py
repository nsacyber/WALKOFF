from os import listdir, walk
from core.helpers import list_apps
from os.path import join, isfile, splitext

#
# Act as an interface for objects to access other event specific variables that might be needed
#

class Context(object):
    def __init__(self):
        #self.workflows = self.getWorkflowsFromFolder()
        self.apps = self.getApps()

        from server.database import User, Role
        from server.appDevice import Device
        from core.controller import controller
        self.controller = controller

        self.User = User
        self.Role = Role
        self.Device = Device

    # Returns list of apps
    # Gets all the app instances
    @staticmethod
    def getApps(path="apps"):
        return list_apps()

    def set(self, key, value):
        setattr(self, key, value)

running_context = Context()
