from core.helpers import list_apps
import core.config.paths

#
# Act as an interface for objects to access other event specific variables that might be needed
#

class Context(object):
    def __init__(self):
        self.apps = self.getApps()

        from server.database import User, Role
        from server.appDevice import Device, App
        from core.controller import controller
        from server.app import app

        self.controller = controller
        self.User = User
        self.Role = Role
        self.Device = Device
        self.App = App
        self.flask_app = app

    # Returns list of apps
    # Gets all the app instances
    @staticmethod
    def getApps(path=core.config.paths.apps_path):
        return list_apps(path=path)

    def set(self, key, value):
        setattr(self, key, value)

    def init_threads(self):
        from core.controller import initialize_threading
        initialize_threading()

    def shutdown_threads(self):
        from core.controller import shutdown_pool
        shutdown_pool()

running_context = Context()
