import json

from walkoff.helpers import get_app_action_default_return, get_app_action_return_is_failure


class ActionResult(object):
    def __init__(self, result, status):
        self.result = result
        self.status = status

    def as_json(self):
        try:
            json.dumps(self.result)
            return {"result": self.result, "status": self.status}
        except TypeError:
            return {"result": str(self.result), "status": self.status}

    def set_default_status(self, app_name, action_name):
        if self.status is None:
            self.status = get_app_action_default_return(app_name, action_name)

    def is_failure(self, app_name, action_name):
        return get_app_action_return_is_failure(app_name, action_name, self.status)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__
