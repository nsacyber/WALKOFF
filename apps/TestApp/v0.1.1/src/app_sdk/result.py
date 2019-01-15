class ActionResult:
    """ Class that formats an ActionResult message """
    def __init__(self, action, result=None, error=None):
        self.result = result
        self.execution_id = action["execution_id"]
        self.action_id = action["id"]
        self.name = action["name"]
        self.action_name = action["action_name"]
        self.app_name = action["app_name"]
        self.error = error

    def to_json(self):
        ret = {"execution_id": self.execution_id, "app_name": self.app_name, "action_name": self.action_name,
               "name": self.name, "action_id": self.action_id, "result": self.result, "error": self.error}
        return ret
