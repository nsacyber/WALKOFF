import enum
import json


class WorkflowEvent(enum.Enum):
    # TODO: Fully flesh this out
    ActionStarted = "ActionStarted"
    ActionSuccess = "ActionSuccess"
    ActionError = "ActionError"

    TransformStarted = "TransformStarted"
    TransformSuccess = "TransformSuccess"
    TransformError = "TransformError"

    ConditionalStarted = "ConditionalStarted"
    ConditionalSuccess = "ConditionalSuccess"
    ConditionalError = "ConditionalError"

    TriggerStarted = "TriggerStarted"
    TriggerSuccess = "TriggerSuccess"
    TriggerError = "TriggerError"

    WorkflowStarted = "WorkflowStarted"
    WorkflowSuccess = "WorkflowSuccess"
    WorkflowError = "WorkflowError"


class MessageJSONDecoder(json.JSONDecoder):
    # TODO: Come up with a way to encode/decode all of these objects reliably
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, o):
        if "error" and "event" in o:
            o["event"] = WorkflowEvent[o["event"]]
            return ActionResult(**o)


class MessageJSONEncoder(json.JSONEncoder):
    """ A custom encoder for encoding Workflow types to JSON strings.
        Note: JSON encoded strings of our custom objects are lossy...for now.
        TODO: Make these not lossy
    """
    def default(self, o):
        if isinstance(o, ActionResult):
            return {"result": o.result, "workflow_execution_id": o.workflow_execution_id, "action_id": o.action_id,
                    "name": o.name, "action_name": o.action_name, "app_name": o.app_name, "error": o.error,
                    "event": o.event}
        elif isinstance(o, WorkflowEvent):
            return o.value


class ActionResult:
    """ Class that formats an ActionResult message """
    def __init__(self, name, action_id, action_name, app_name, workflow_execution_id, result=None, error=None, event=None):
        self.name = name
        self.action_id = action_id
        self.action_name = action_name
        self.app_name = app_name
        self.workflow_execution_id = workflow_execution_id
        self.result = result
        self.error = error
        self.event = event

    @classmethod
    def from_action(cls, action, result=None, error=None, event=None):
        workflow_execution_id = action.workflow_execution_id
        action_id = action._id
        name = action.name
        action_name = action.action_name
        app_name = action.app_name
        return cls(name, action_id, action_name, app_name, workflow_execution_id, result, error, event)
