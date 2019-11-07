import enum
import json
import datetime


def message_dumps(obj):
    return json.dumps(obj, cls=MessageJSONEncoder)


def message_loads(obj):
    return json.loads(obj, cls=MessageJSONDecoder)


def message_dump(obj, fp):
    return json.dump(obj, fp, cls=MessageJSONEncoder)


def message_load(obj):
    return json.load(obj, cls=MessageJSONDecoder)


class MessageJSONDecoder(json.JSONDecoder):
    """ A custom decoder for decoding JSON strings to Message types. """

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, o):
        if "result" in o and "app_name" in o:
            o["status"] = StatusEnum[o["status"]]
            return NodeStatusMessage(**o)

        elif "workflow_id" in o and "execution_id" in o:
            o["status"] = StatusEnum[o["status"]]
            return WorkflowStatusMessage(**o)

        elif "trigger_data" in o:
            return TriggerMessage(**o)

        else:
            return o


class MessageJSONEncoder(json.JSONEncoder):
    """ A custom encoder for encoding Message types to JSON strings. """

    def default(self, o):
        if isinstance(o, NodeStatusMessage):
            r = {"name": o.name, "node_id": o.node_id, "label": o.label, "app_name": o.app_name,
                 "execution_id": o.execution_id, "result": o.result, "status": o.status,
                 "started_at": o.started_at, "completed_at": o.completed_at, "combined_id": o.combined_id,
                 "parameters": o.parameters}

            try:
                json.dumps(o.result)
            except (TypeError, ValueError):
                r["result"] = f"Node returned result of type '{type(o.result)}' which is not JSON serializable."
                r["status"] = StatusEnum.FAILURE
            finally:
                return r

        elif isinstance(o, WorkflowStatusMessage):
            return {"execution_id": o.execution_id, "workflow_id": o.workflow_id, "name": o.name, "status": o.status,
                    "started_at": o.started_at, "completed_at": o.completed_at, "user": o.user,
                    "app_name": o.app_name, "action_name": o.action_name, "label": o.label}

        elif isinstance(o, TriggerMessage):
            return {"trigger_data": o.trigger_data}

        elif isinstance(o, JSONPatch):
            if o.op in JSONPatchOps:
                return {k: getattr(o, k, None) for k in o.__slots__ if getattr(o, k, None) is not None}
            else:
                raise ValueError("Improper JSON Patch operation")

        elif isinstance(o, StatusEnum):
            return o.value

        elif isinstance(o, JSONPatchOps):
            return o.value.lower()

        elif isinstance(o, JSONPatch):
            return {k: getattr(o, k, None) for k in o.__slots__ if getattr(o, k, None) is not None}

        elif isinstance(o, datetime.datetime):
            return str(o)

        else:
            return o


class JSONPatch:
    __slots__ = ("op", "path", "value", "from_")

    def __init__(self, op=None, path=None, value=None, from_=None):
        self.op = op
        self.path = path
        self.value = value
        self.from_ = from_


class JSONPatchOps(str, enum.Enum):
    TEST = "test"
    REMOVE = "remove"
    ADD = "add"
    REPLACE = "replace"
    MOVE = "move"
    COPY = "copy"


class StatusEnum(str, enum.Enum):
    """ Holds statuses used for Workflow and Action status messages """
    PAUSED = "PAUSED"  # not currently implemented but may be if we see a use case
    AWAITING_DATA = "AWAITING_DATA"  # possibly for triggers?
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    EXECUTING = "EXECUTING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class WorkflowStatusMessage(object):
    """ Class that formats a WorkflowStatusMessage message """
    __slots__ = ("execution_id", "workflow_id", "name", "status", "started_at", "completed_at",
                 "user", "app_name", "action_name", "label")

    def __init__(self, execution_id, workflow_id, name, started_at=None, completed_at=None, status=None,
                 user=None, app_name=None, action_name=None, label=None):
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        self.name = name
        self.status = status
        self.started_at = started_at
        self.completed_at = completed_at
        self.user = user
        self.app_name = app_name
        self.action_name = action_name
        self.label = label

    @classmethod
    def execution_pending(cls, execution_id, workflow_id, name, user=None, app_name=None, action_name=None, label=None):
        return cls(execution_id, workflow_id, name, status=StatusEnum.PENDING, user=user,
                   app_name=app_name, action_name=action_name, label=label)

    @classmethod
    def execution_started(cls, execution_id, workflow_id, name, user=None, app_name=None, action_name=None, label=None):
        start_time = datetime.datetime.now()
        return cls(execution_id, workflow_id, name, started_at=start_time, status=StatusEnum.EXECUTING, user=user,
                   app_name=app_name, action_name=action_name, label=label)

    @classmethod
    def execution_continued(cls, execution_id, workflow_id, name, user=None, app_name=None, action_name=None, label=None):
        return cls(execution_id, workflow_id, name, status=StatusEnum.EXECUTING, user=user,
                   app_name=app_name, action_name=action_name, label=label)

    @classmethod
    def execution_completed(cls, execution_id, workflow_id, name, user=None, app_name=None, action_name=None, label=None):
        end_time = datetime.datetime.now()
        return cls(execution_id, workflow_id, name, completed_at=end_time, status=StatusEnum.COMPLETED, user=user,
                   app_name=app_name, action_name=action_name, label=label)

    @classmethod
    def execution_aborted(cls, execution_id, workflow_id, name, user=None, app_name=None, action_name=None, label=None):
        end_time = datetime.datetime.now()
        return cls(execution_id, workflow_id, name, completed_at=end_time, status=StatusEnum.ABORTED, user=user,
                   app_name=app_name, action_name=action_name, label=label)


class NodeStatusMessage(object):
    """ Class that formats a NodeStatusMessage message. """
    __slots__ = ("name", "node_id", "label", "app_name", "execution_id", "parameters", "combined_id", "result",
                 "status", "started_at", "completed_at")

    def __init__(self, name, node_id, label, app_name, execution_id, combined_id=None, parameters=None, result=None,
                 status=None, started_at=None, completed_at=None):
        self.name = name
        self.node_id = node_id
        self.label = label
        self.app_name = app_name
        self.execution_id = execution_id
        self.combined_id = combined_id if combined_id is not None else ':'.join((node_id, execution_id))
        self.result = result
        self.parameters = parameters
        self.status = status
        self.started_at = started_at
        self.completed_at = completed_at

    @classmethod
    def from_node(cls, node, execution_id, result=None, status=None, started_at=None, completed_at=None, parameters=None):
        return cls(node.name, node.id_, node.label, node.app_name, execution_id, result=result,
                   status=status, started_at=started_at, completed_at=completed_at, parameters=parameters)

    @classmethod
    def pending_from_node(cls, node, execution_id, parameters=None):
        return cls(node.name, node.id_, node.label, node.app_name, execution_id, status=StatusEnum.PENDING,
                   parameters=parameters)

    @classmethod
    def executing_from_node(cls, node, execution_id, parameters=None, started_at=None):
        return cls(node.name, node.id_, node.label, node.app_name, execution_id, started_at=started_at,
                   status=StatusEnum.EXECUTING, parameters=parameters)

    @classmethod
    def success_from_node(cls, node, execution_id, result, parameters=None, started_at=None):
        completed_at = datetime.datetime.now()
        return cls(node.name, node.id_, node.label, node.app_name, execution_id, result=result, started_at=started_at,
                   completed_at=completed_at, status=StatusEnum.SUCCESS, parameters=parameters)

    @classmethod
    def failure_from_node(cls, node, execution_id, result, parameters=None, started_at=None):
        completed_at = datetime.datetime.now()
        return cls(node.name, node.id_, node.label, node.app_name, execution_id, result=result, started_at=started_at,
                   completed_at=completed_at, status=StatusEnum.FAILURE, parameters=parameters)

    @classmethod
    def aborted_from_node(cls, node, execution_id, parameters=None, started_at=None):
        completed_at = datetime.datetime.now()
        return cls(node.name, node.id_, node.label, node.app_name, execution_id, completed_at=completed_at,
                   started_at=started_at, status=StatusEnum.ABORTED, parameters=parameters)


class TriggerMessage(object):
    """ Class that formats a TriggerMessage. """
    __slots__ = ("trigger_data",)

    def __init__(self, trigger_data):
        self.trigger_data = trigger_data
