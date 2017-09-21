from core.helpers import list_apps, list_widgets
import core.config.paths


class Context(object):
    def __init__(self):
        """Initializes a new Context object. This acts as an interface for objects to access other event specific
            variables that might be needed.
        """
        self.apps = self.get_apps()

        from server.app import app
        from server.database import User, Role, resource_roles, db
        from server.triggers import Triggers
        from server.casesubscription import CaseSubscription
        import core.controller
        from server.scheduledtasks import ScheduledTask

        self.User = User
        self.Role = Role
        self.Triggers = Triggers
        self.CaseSubscription = CaseSubscription
        self.flask_app = app
        self.resource_roles = resource_roles
        self.db = db
        self.controller = core.controller.controller
        self.ScheduledTask = ScheduledTask

    @staticmethod
    def get_apps(path=core.config.paths.apps_path):
        """Gets all the App instances.
        
        Args:
            path (str, optional): The path to the apps. Defaults to the apps_path set in the configuration.
            
        Returns:
            A list of App instances.
        """
        return list_apps(path=path)

    @staticmethod
    def get_widgets(path=core.config.paths.apps_path):
        """Gets a dictionary of all Widgets for every App.
        
        Args:
            path (str, optional): The path to the apps. Defaults to the apps_path set in the configuration.
            
        Returns:
            A dictionary containing all App objects and any Widgets associated with them.
        """
        ret = []
        for app in Context.get_apps():
            for widget in list_widgets(app, path):
                ret.append({'app': app, 'widget': widget})
        return ret

    def set(self, key, value):
        """Sets an attribute for the object.
        
        Args:
            key (str): The name of the attribute to set.
            value (any): The value of the attribute to set.
        """
        setattr(self, key, value)

running_context = Context()
