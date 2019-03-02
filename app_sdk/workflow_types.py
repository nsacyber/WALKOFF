import uuid
import json
import enum
import logging
from collections import namedtuple, deque

from networkx import DiGraph

logger = logging.getLogger("WALKOFF")

Point = namedtuple("Point", ("x", "y"))
Branch = namedtuple("Branch", ("source", "destination"))


class ParameterVariant(enum.Enum):
    STATIC_VALUE = "STATIC_VALUE"
    ACTION_RESULT = "ACTION_RESULT"
    WORKFLOW_VARIABLE = "WORKFLOW_VARIABLE"
    GLOBAL = "GLOBAL"


class WorkflowJSONDecoder(json.JSONDecoder):
    # TODO: Come up with a way to encode/decode all of these objects reliably
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)
        self.actions = {}

    def object_hook(self, o):
        if "x" and "y" in o:
            return Point(**o)

        elif "action_name" and "app_name" in o:
            action = Action(**o)
            self.actions[action.id_] = action
            return action

        elif "variant" in o:
            o["variant"] = ParameterVariant[o["variant"]]
            return Parameter(**o)

        elif "source" and "destination" in o:
            return Branch(source=self.actions[o["source"]], destination=self.actions[o["destination"]])

        elif "conditional" in o:
            return Condition(**o)

        elif "transform" in o:
            return Transform(**o)

        elif "trigger" in o:
            return Trigger(**o)

        elif "description" and "value" in o:
            return WorkflowVariable(**o)

        elif "actions" and "branches" in o:
            workflow_variables = {var.id_: var for var in o["workflow_variables"]}
            o["workflow_variables"] = workflow_variables
            return Workflow(**o)


class WorkflowJSONEncoder(json.JSONEncoder):
    """ A custom encoder for encoding Workflow types to JSON strings.
        Note: JSON encoded strings of our custom objects are lossy...for now.
        TODO: Make these not lossy
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.workflow = {}

    def default(self, o):
        if isinstance(o, Workflow):
            branches = [{"source": src.id_, "destination": dst.id_} for src, dst in o.edges]
            actions = [node for node in o.nodes]
            conditions = [condition for condition in o.conditions]
            transforms = [transform for transform in o.transforms]
            triggers = [trigger for trigger in o.triggers]
            workflow_variables = list(o.workflow_variables.values())
            return {"id_": o.id_, "execution_id": o.execution_id, "name": o.name, "start": o.start.id_,
                    "actions": actions, "conditions": conditions, "branches": branches, "transforms": transforms,
                    "triggers": triggers, "workflow_variables": workflow_variables, "is_valid": o.is_valid,
                    "errors": None}

        elif isinstance(o, Action):
            return {"id_": o.id_, "app_name": o.app_name, "action_name": o.action_name, "name": o.name,
                    "parameters": o.parameters, "priority": o.priority, "position": o.position,
                    "workflow_execution_id": o.workflow_execution_id}

        elif isinstance(o, Parameter):
            return {"name": o.name, "variant": o.variant, "value": o.value, "reference": o.reference}

        elif isinstance(o, ParameterVariant):
            return o.value

        elif isinstance(o, WorkflowVariable):
            return {"description": o.description, "id_": o.id_, "name": o.name, "value": o.value}


class Node:
    def __init__(self, name, position: Point, id_=None):
        self.id_ = id_ if id_ is not None else str(uuid.uuid4())
        self.name = name
        self.position = position

    def __repr__(self):
        return f"Node-{self.id_}"

    def __str__(self):
        return f"Node-{self.name}"


class Parameter:
    def __init__(self, name, value=None, variant=None, reference=None):
        self.name = name
        self.value = value
        self.variant: ParameterVariant = variant
        self.reference = reference
        self.validate()

    def __str__(self):
        return f"Parameter-{self.name}:{self.value or self.reference}"

    def validate(self):
        """Validates the param"""
        message = None
        reference_variants = {ParameterVariant.ACTION_RESULT, ParameterVariant.GLOBAL,
                              ParameterVariant.WORKFLOW_VARIABLE}
        if self.value is None and not self.reference:
            message = f'Input {self.name} must have either value or reference. Input has neither'
            logger.error(message)

        elif self.value is not None and self.reference:
            message = f'Input {self.name} must have either value or reference. Input has both. Using "value"'
            logger.warning(message)
            self.reference = None

        elif self.reference and self.variant not in reference_variants:
            message = 'Reference input must specify the variant.'
            logger.error(message)
        return message


class WorkflowVariable:
    # Previously EnvironmentVariable
    def __init__(self, id_, name, value, description=None):
        self.id_ = id_
        self.name = name
        self.value = value
        self.description = description


class Action(Node):
    def __init__(self, name, position, app_name, action_name, priority, workflow_execution_id=None, parameters=None,
                 id_=None):
        super().__init__(name, position, id_)
        self.app_name = app_name
        self.action_name = action_name
        self.workflow_execution_id = workflow_execution_id
        self.parameters = parameters if parameters is not None else list()
        self.priority = priority

    def __str__(self):
        return f"Action: {self.name}::{self.id_}::{self.workflow_execution_id}"

    def __repr__(self):
        return f"Action: {self.name}::{self.id_}::{self.workflow_execution_id}"

    def __gt__(self, other):
        return self.priority > other.priority

    @classmethod
    def from_json(cls, data):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                logger.exception("Error parsing Action from JSON.")
                return
        try:
            return cls(name=data["name"], action_name=data["action_name"], app_name=data["app_name"],
                       parameters=data["parameters"], priority=data["priority"],
                       position=Point(data["position"]["x"], data["position"]["y"]), id_=data["id"])

        except KeyError:
            logger.exception("Error parsing Action from JSON.")


class Condition(Node):
    def __init__(self, name, position: Point, conditional=None):
        super().__init__(name, position)
        self.conditional = conditional

    @staticmethod
    def from_json(data):
        pass

    @staticmethod
    def to_json(data):
        pass


# TODO: fully realize and implement triggers
class Trigger(Node):
    def __init__(self, name, position: Point, trigger):
        super().__init__(name, position)
        self.trigger = trigger

    @staticmethod
    def from_json(data):
        pass

    @staticmethod
    def to_json(data):
        pass


class Transform(Node):
    def __init__(self, name, position: Point, transform, transform_arg=None):
        super().__init__(name, position)
        self.transform = f"__{transform.lower()}"
        self.transform_arg = transform_arg

    def __call__(self, data):
        """ Execute an action and ship its result """
        logger.debug(f"Attempting execution of: {self.name}-{self.id_}")
        if hasattr(self, self.transform):
            try:
                if self.transform_arg is None:
                    result = getattr(self, self.transform)(data=data)
                else:
                    result = getattr(self, self.transform)(self.transform_arg, data=data)
                logger.debug(f"Executed {self.name}-{self.id_} with result: {result}")

            # TODO: figure out which exceptions will be thrown by which failed transforms and handle them
            except Exception:
                logger.exception(f"Failed to execute {self.name}-{self.id_}")

        else:
            logger.error(f"{self.__class__.__name__} has no method {self.transform}")

    # TODO: add JSON to CSV parsing and vice versa.
    def __get_value_at_index(self, index, data=None):
        return data[index]

    def __get_value_at_key(self, key, data=None):
        return data[key]

    def __split_string_to_array(self, delimiter=' ', data=None):
        return data.split(delimiter)


class Workflow(DiGraph):
    def __init__(self, name, start, actions: [Action], conditions: [Condition], triggers: [Trigger],
                 transforms: [Transform], branches: [Branch], id_=None, execution_id=None, workflow_variables=None,
                 is_valid=None, errors=None):
        super().__init__()
        for branch in branches:
            self.add_edge(branch.source, branch.destination)
        self.add_nodes_from(actions)
        self.start = next(filter(lambda action: action.id_ == start, actions))  # quick search to find the start node
        self.id_ = id_ if id_ is not None else str(uuid.uuid4())
        self.is_valid = is_valid if is_valid is not None else self.validate()
        self.name = name
        self.execution_id = execution_id
        self.workflow_variables = workflow_variables
        self.conditions = conditions
        self.transforms = transforms
        self.triggers = triggers
        self.errors = errors

    def validate(self):
        # TODO: add in workflow validation from old implementation
        return True

    @staticmethod
    def dereference_environment_variables(data):
        return {ev["id"]: (ev["name"], ev["value"]) for ev in data.get("environment_variables", [])}

    @classmethod
    def from_json(cls, data):
        # TODO: make this not a hack to work with the old crap

        # Design our workflow
        actions = {}
        branches = set()

        for action in data.get("actions", []):
            # Get action priority
            action["priority"] = 3
            for branch in data.get("branches", []):
                if action["id"] == branch["destination"]:
                    action["priority"] = branch["priority"]
                    break

            # Get action params
            action["parameters"] = set()
            for param in action.get("arguments", []):
                action["parameters"].add(Parameter(name=param["name"], value=param.get("value", None),
                                                   reference=param.get("reference", None),
                                                   variant=param.get("variant", None)))

            actions[action["id"]] = Action.from_json(action)

        for branch in data.get("branches", []):
            branches.add(Branch(actions[branch["source"]], actions[branch["destination"]]))

        workflow = Workflow(name=data["name"], start=actions[data["start"]], actions=set(actions.values()),
                            branches=branches, id_=data.get("workflow_id", uuid.uuid4()),
                            execution_id=data["execution_id"],
                            workflow_variables=Workflow.dereference_environment_variables(data))
        return workflow

    def get_dependents(self, node):
        """
            BFS to get all nodes dependent on the current node. This includes the current node.
        """
        visited = {node}
        queue = deque([node])

        while queue:
            node = queue.pop()
            children = set(self.successors(node))
            for child in children:
                if child not in visited:
                    queue.appendleft(child)
                    visited.add(child)

        return visited


if __name__ == "__main__":
    def workflow_dump(fp):
        return json.dump(fp, cls=WorkflowJSONEncoder)

    def workflow_dumps(obj):
        return json.dumps(obj, cls=WorkflowJSONEncoder)


    def workflow_load(fp):
        return json.load(fp, cls=WorkflowJSONDecoder)


    def workflow_loads(obj):
        return json.loads(obj, cls=WorkflowJSONDecoder)


    with open("../data/workflows/hello.json") as fp:
        wf = workflow_load(fp)
        wf_str = workflow_dumps(wf)
        wf2 = workflow_loads(wf_str)
        wf2_str = workflow_dumps(wf2)
        print(wf_str == wf2_str)
