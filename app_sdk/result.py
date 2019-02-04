# TODO: Make this not a hack for the demo
ActionStarted = "ActionStarted"
ActionExecutionSuccess = "ActionExecutionSuccess"
ActionExecutionError = "ActionExecutionError"


class ActionResult:
    """ Class that formats an ActionResult message """
    def __init__(self, action, result=None, error=None, status=None):
        self.result = result
        self.execution_id = action["execution_id"]
        self.workflow_execution_id = action["workflow_execution_id"]
        self.action_id = action["id"]
        self.name = action["name"]
        self.action_name = action["action_name"]
        self.app_name = action["app_name"]
        self.error = error
        self.status = status
        self.arguments = action["params"] if action["params"] is not None else []

    def to_json(self):
        ret = {"execution_id": self.execution_id, "app_name": self.app_name, "action_name": self.action_name,
               "name": self.name, "action_id": self.action_id, "result": self.result, "error": self.error,
               "arguments": self.arguments, "status": self.status, "id": self.action_id,
               "data": {"result": self.result}, "workflow": {"execution_id": self.workflow_execution_id}}
        return ret

