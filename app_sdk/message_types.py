import enum
import json
import time
from collections import namedtuple


def message_dumps(obj):
    return json.dumps(obj, cls=MessageJSONEncoder)


def message_loads(obj):
    return json.loads(obj, cls=MessageJSONDecoder)


def message_dump(obj):
    return json.dumps(obj, cls=MessageJSONEncoder)


def message_load(obj):
    return json.loads(obj, cls=MessageJSONDecoder)


class MessageJSONDecoder(json.JSONDecoder):
    """ A custom decoder for decoding JSON strings to Message types. """
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, o):
        if "action_id" and "app_name" in o:
            o["status"] = StatusEnum[o["status"]]
            return ActionStatus(**o)

        elif "workflow_id" and "execution_id" in o:
            o["status"] = StatusEnum[o["status"]]
            return WorkflowStatus(**o)


class MessageJSONEncoder(json.JSONEncoder):
    """ A custom encoder for encoding Message types to JSON strings. """
    def default(self, o):
        if isinstance(o, ActionStatus):
            return {"name": o.name, "action_id": o.action_id, "action_name": o.action_name, "app_name": o.app_name,
                    "workflow_execution_id": o.workflow_execution_id, "result": o.result,  "error": o.error,
                    "status": o.status}

        elif isinstance(o, WorkflowStatus):
            return {"execution_id": o.execution_id, "workflow_id": o.workflow_id, "name": o.name, "status": o.status,
                    "started_at": o.started_at, "completed_at": o.completed_at, "user": o.user}

        elif isinstance(o, JSONPatch):
            if o.op in JSONPatchOps:
                ret = {"op": o.op, "path": o.path}

                if o.op in JSONPatchOps.requires_value.value:
                    if o.value is not None:
                        ret["value"] = o.value
                    else:
                        raise ValueError(f"Value must be provided for JSONPatch Op: {o.op}")
                if o.op in JSONPatchOps.requires_from.value:
                    if o.from_ is not None:
                        ret["from"] = o.from_
                    else:
                        raise ValueError(f"From must be provided for JSONPatch Op: {o.op}")

                return ret
            else:
                raise ValueError("Improper JSON Patch operation")

        elif isinstance(o, StatusEnum):
            return o.value


JSONPatch = namedtuple("JSONPatch", ("op", "path", "value", "from_"), defaults=(None, None))


class JSONPatchOps(enum.Enum):
    TEST = "TEST"
    REMOVE = "REMOVE"
    ADD = "ADD"
    REPLACE = "REPLACE"
    MOVE = "MOVE"
    COPY = "COPY"

    requires_value = {TEST, ADD, REPLACE}
    requires_from = {MOVE, COPY}


class StatusEnum(enum.Enum):
    """ Holds statuses used for Workflow and Action status messages """
    PAUSED = "PAUSED"  # not currently implemented but may be if we see a use case
    AWAITING_DATA = "AWAITING_DATA"  # possibly for triggers?
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    EXECUTING = "EXECUTING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class WorkflowStatus:
    """ Class that formats a WorkflowStatusMessage message """
    def __init__(self, execution_id, workflow_id, name, started_at=None, completed_at=None, status=None, user=None):
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        self.name = name
        self.status = status
        self.started_at = started_at
        self.completed_at = completed_at
        self.user = user

    @classmethod
    def execution_pending(cls, execution_id, workflow_id, name, user=None):
        return cls(execution_id, workflow_id, name, status=StatusEnum.PENDING, user=user)

    @classmethod
    def execution_started(cls, execution_id, workflow_id, name, user=None):
        start_time = time.time()
        return cls(execution_id, workflow_id, name, started_at=start_time, status=StatusEnum.EXECUTING, user=user)

    @classmethod
    def execution_completed(cls, execution_id, workflow_id, name, user=None):
        end_time = time.time()
        return cls(execution_id, workflow_id, name, completed_at=end_time, status=StatusEnum.COMPLETED, user=user)

    @classmethod
    def execution_aborted(cls, execution_id, workflow_id, name, user=None):
        end_time = time.time()
        return cls(execution_id, workflow_id, name, completed_at=end_time, status=StatusEnum.ABORTED, user=user)


class ActionStatus:
    """ Class that formats an ActionStatusMessage message. The name is a bit of a misnomer since they are used for Trigger,
        Transform, and Condition messages as well. NodeStatus just didn't seem like the right thing to call them.
    """
    def __init__(self, name, action_id, action_name, app_name, workflow_execution_id, result=None, error=None,
                 status=None, started_at=None, completed_at=None):
        self.name = name
        self.action_id = action_id
        self.action_name = action_name
        self.app_name = app_name
        self.workflow_execution_id = workflow_execution_id
        self.result = result
        self.error = error
        self.status = status
        self.started_at = started_at
        self.completed_at = completed_at

    @classmethod
    def from_action(cls, action, result=None, error=None, status=None, started_at=None, completed_at=None):
        workflow_execution_id = action.workflow_execution_id
        action_id = action.id_
        name = action.name
        action_name = action.action_name
        app_name = action.app_name
        started_at = started_at
        completed_at = completed_at
        return cls(name, action_id, action_name, app_name, workflow_execution_id, result=result, error=error,
                   status=status, started_at=started_at, completed_at=completed_at)

    @classmethod
    def pending_from_action(cls, action):
        return ActionStatus.from_action(action, status=StatusEnum.PENDING)

    @classmethod
    def executing_from_action(cls, action):
        started_at = time.time()
        return ActionStatus.from_action(action, started_at=started_at, status=StatusEnum.EXECUTING)

    @classmethod
    def success_from_action(cls, action, result):
        completed_at = time.time()
        return ActionStatus.from_action(action, result=result, completed_at=completed_at, status=StatusEnum.SUCCESS)

    @classmethod
    def failure_from_action(cls, action, error=None):
        completed_at = time.time()
        return ActionStatus.from_action(action, error=error, completed_at=completed_at, status=StatusEnum.FAILURE)
