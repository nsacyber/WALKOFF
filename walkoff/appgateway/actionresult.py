import json

from walkoff.appgateway.apiutil import get_app_action_default_return, get_app_action_return_is_failure
from walkoff.helpers import format_exception_message

class ActionResult(object):
    def __init__(self, result, status):
        """ActionResult object, which stores the result of an action

        Args:
            result (str): The returned result from the action
            status (str): The status of the action, success or error
        """
        self.result = result
        self.status = status

    def as_json(self):
        """Displays the object

        Returns:
            (dict): Dict containing the result and the status
        """
        try:
            json.dumps(self.result)
            return {"result": self.result, "status": self.status}
        except TypeError:
            return {"result": str(self.result), "status": self.status}

    def set_default_status(self, app_name, action_name):
        """Set the default status for an action

        Args:
            app_name (str): The app name for the action
            action_name (str): The action name
        """
        if self.status is None:
            self.status = get_app_action_default_return(app_name, action_name)

    def is_failure(self, app_name, action_name):
        """Checks the api for whether a status code is a failure code for a given app and action

        Args:
            app_name (str): Name of the app
            action_name (str): Name of the action

        Returns:
            (bool): True if status is a failure code, false otherwise
        """
        return get_app_action_return_is_failure(app_name, action_name, self.status)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @classmethod
    def from_exception(cls, exc, status):
        formatted_error = format_exception_message(exc)
        return cls('error: {0}'.format(formatted_error), status)
