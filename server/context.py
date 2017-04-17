from core.helpers import list_apps
import core.config.paths


class Context(object):
    """
    Act as an interface for objects to access other event specific variables that might be needed
    """
    def __init__(self):
        self.apps = self.get_apps()

        from server.app import app
        from server.appdevice import Device, App
        from server.database import User, Role, userRoles, db, user_datastore
        from server.triggers import Triggers
        from core.controller import controller

        self.User = User
        self.Role = Role
        self.Device = Device
        self.App = App
        self.Triggers = Triggers
        self.flask_app = app
        self.user_roles = userRoles
        self.db = db
        self.user_datastore = user_datastore
        self.controller = controller

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
