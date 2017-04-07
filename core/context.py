from core.helpers import list_apps
import core.config.paths


class Context(object):
    """
    Act as an interface for objects to access other event specific variables that might be needed
    """
    def __init__(self):
        self.apps = self.get_apps()

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
    def get_apps(path=core.config.paths.apps_path):
        return list_apps(path=path)

    def set(self, key, value):
        setattr(self, key, value)

    @staticmethod
    def init_threads():
        from core.controller import initialize_threading
        initialize_threading()

    @staticmethod
    def shutdown_threads():
        from core.controller import shutdown_pool
        shutdown_pool()

running_context = Context()
