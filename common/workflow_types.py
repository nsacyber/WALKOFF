import uuid
import json
import logging
from collections import namedtuple

from networkx import DiGraph


logger = logging.getLogger("WALKOFF")

Point = namedtuple("Point", ("x", "y"))
Branch = namedtuple("Branch", ("src", "dst"))


class WorkflowJSONDecoder(json.JSONDecoder):
    # TODO: Come up with a way to encode/decode all of these objects reliably
    pass


class WorkflowJSONEncoder(json.JSONEncoder):
    """ A custom encoder for encoding Workflow types to JSON strings.
        Note: JSON encoded strings of our custom objects are lossy...for now.
        TODO: Make these not lossy
    """
    def default(self, o):
        if isinstance(o, set):
            elem = None
            for elem in o: break  # This is the fastest way to get an element from a set without removing it.

            if elem is None:
                return None

            if isinstance(elem, Param):  # Convert sets of Params to dicts of name:value pairs
                return dict((elem.name, elem.value) for elem in o)

            return list(o)  # Any other set of objects should fine as a JSON array.

        if isinstance(o, Workflow):
            return

        elif isinstance(o, Action):
            return {"execution_id": o.execution_id, "app_name": o.app_name, "action_name": o.action_name,
                    "params": o.params, "name": o.name, "id": o.id, "pos": o.pos,
                    "workflow_execution_id": o.workflow_execution_id}

        elif isinstance(o, Param):
            return {o.name: o.value}


class Node:
    def __init__(self, name, pos: Point, _id):
        self.id = _id if _id is not None else str(uuid.uuid4())
        self.name = name
        self.pos = pos

    def __repr__(self):
        return f"Node-{self.id}"

    def __str__(self):
        return f"Node-{self.name}"


class Param:
    def __init__(self, name, value=None, reference=None):
        """Initializes an Argument object.

        Args:
            name (str): The name of the Argument.
            value (any, optional): The value of the Argument. Defaults to None. Value or reference must be included.
            reference (int, optional): The ID of the Action from which to grab the result. Defaults to None.
                If value is not provided, then reference must be included.

        """
        super().__init__()
        self.name = name
        self.value = value
        self._is_reference = True if value is None else False
        self.reference = reference
        self.validate()

    def validate(self):
        """Validates the object"""
        self.errors = []
        if self.value is None and not self.reference:
            message = 'Input {} must have either value or reference. Input has neither'.format(self.name)
            logger.error(message)
            self.errors = [message]

        elif self.value is not None and self.reference:
            message = 'Input {} must have either value or reference. Input has both. Using "value"'.format(self.name)
            logger.warning(message)
            self.reference = None


class Action(Node):
    def __init__(self, display_name, action_name, app_name, params: [Param], priority, pos: Point, _id=None):
        super().__init__(display_name, pos, _id)
        self.execution_id = None
        self.workflow_execution_id = None
        self.app_name = app_name
        self.action_name = action_name
        self.params = params
        self.priority = priority

    def __str__(self):
        return f"Action: {self.name}::{self.id}::{self.execution_id}"

    def __repr__(self):
        return f"Action: {self.name}::{self.id}::{self.execution_id}"

    def __gt__(self, other):
        return self.priority > other.priority

    def to_json(self):
        ret = {"execution_id": self.execution_id, "app_name": self.app_name, "action_name": self.action_name,
               "params": self.params, "name": self.name, "id": self.id, "pos": self.pos}
        return ret

    @classmethod
    def from_json(cls, data):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                logger.exception("Error parsing Action from JSON.")
                return
        try:
            return cls(display_name=data["name"], action_name=data["action_name"], app_name=data["app_name"],
                       params=data["params"], priority=data["priority"],
                       pos=Point(data["position"]["x"], data["position"]["y"]), _id=data["id"])

        except KeyError:
            logger.exception("Error parsing Action from JSON.")


class Condition(Node):
    def __init__(self, name, pos: Point):
        super().__init__(name, pos)

    @staticmethod
    def from_json(data):
        pass

    @staticmethod
    def to_json(data):
        pass


class Trigger(Node):
    def __init__(self, name, pos: Point):
        super().__init__(name, pos)

    @staticmethod
    def from_json(data):
        pass

    @staticmethod
    def to_json(data):
        pass


class Transform(Node):
    def __init__(self, name, pos: Point):
        super().__init__(name, pos)

    @staticmethod
    def from_json(data):
        pass

    @staticmethod
    def to_json(data):
        pass


class Workflow(DiGraph):
    def __init__(self, name, start: Action, actions: [Action], branches: [Branch], _id=None,
                 execution_id=None, environment_variables=None):
        super().__init__()
        for branch in branches:
            self.add_edge(branch.src, branch.dst)
        self.add_nodes_from(actions)
        self.start = start
        self.id = _id if _id is not None else str(uuid.uuid4())
        self.is_valid = self.is_valid()
        self.name = name
        self.execution_id = execution_id
        self.environment_variables = environment_variables

    def is_valid(self):
        # TODO: add in workflow validation from old implementation
        return True

    @staticmethod
    def dereference_environment_variables(data):
        return {ev["id"]: (ev["name"], ev["value"]) for ev in data.get("environment_variables", [])}

    @classmethod
    def from_json(cls, data):
        # TODO: make this not a hack to work with the old crap
        if data.get("workflow"):  # if coming from api-gateway in new format
            data["workflow"]["execution_id"] = data["execution_id"]
            data["workflow"]["workflow_id"] = data["workflow_id"]
            data = data["workflow"]

        # Design our workflow
        actions = {}
        branches = set()

        for action in data.get("actions", []):
            # Get action priority
            action["priority"] = 3
            for branch in data.get("branches", []):
                if action["id"] == branch["destination_id"]:
                    action["priority"] = branch["priority"]
                    break

            # Get action params
            action["params"] = set()
            for param in action.get("arguments", []):
                action["params"].add(Param(name=param["name"], value=param.get("value", None),
                                           reference=param.get("reference", None)))

            actions[action["id"]] = Action.from_json(action)

        for branch in data.get("branches", []):
            branches.add(Branch(actions[branch["source_id"]], actions[branch["destination_id"]]))

        workflow = Workflow(name=data["name"], start=actions[data["start"]], actions=set(actions.values()),
                            branches=branches, _id=data["workflow_id"], execution_id=data["execution_id"],
                            environment_variables=Workflow.dereference_environment_variables(data))
        return workflow

    def to_json(self, data):
        # TODO: map Workflow object to json workflow
        pass
