import core.config.paths
from core.helpers import list_apps


class Context(object):
    def __init__(self):
        """Initializes a new Context object. This acts as an interface for objects to access other event specific
            variables that might be needed.
        """
        self.apps = self.get_apps()

        from server.app import app
        from server.database import User, Role, db
        from server.casesubscription import CaseSubscription
        import core.controller
        from server.scheduledtasks import ScheduledTask
        from server.messaging import Message

        self.User = User
        self.Role = Role
        self.CaseSubscription = CaseSubscription
        self.flask_app = app
        self.db = db
        self.controller = core.controller.controller
        self.ScheduledTask = ScheduledTask
        self.Message = Message

    @staticmethod
    def get_apps(path=core.config.paths.apps_path):
        """Gets all the App instances.
        
        Args:
            path (str, optional): The path to the apps. Defaults to the apps_path set in the configuration.
            
        Returns:
            A list of App instances.
        """
        return list_apps(path=path)

    def set(self, key, value):
        """Sets an attribute for the object.
        
        Args:
            key (str): The name of the attribute to set.
            value (any): The value of the attribute to set.
        """
        setattr(self, key, value)


running_context = Context()
