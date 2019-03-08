import uuid
import json
import enum
import logging
from collections import namedtuple, deque

from networkx import DiGraph
from asteval import Interpreter, make_symbol_table

logger = logging.getLogger("WALKOFF")


def workflow_dumps(obj):
    return json.dumps(obj, cls=WorkflowJSONEncoder)


def workflow_loads(obj):
    return json.loads(obj, cls=WorkflowJSONDecoder)


def workflow_dump(obj):
    return json.dump(obj, fp, cls=WorkflowJSONEncoder)


def workflow_load(obj):
    return json.load(obj, cls=WorkflowJSONDecoder)


class ConditionException(Exception):
    pass


class WorkflowJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)
        self.nodes = {}
        self.branches = set()

    def object_hook(self, o):
        if "x" and "y" in o:
            return Point(**o)

        elif "parameters" and "priority" in o:
            node = Action(**o)
            self.nodes[node.id_] = node
            return node

        elif "variant" in o:
            o["variant"] = ParameterVariant[o["variant"]]
            return Parameter(**o)

        elif "source" and "destination" in o:
            self.branches.add(Branch(source=o["source"], destination=o["destination"]))

        elif "conditional" in o:
            node = Condition(**o)
            self.nodes[node.id_] = node
            return node

        elif "transform" in o:
            node = Transform(**o)
            self.nodes[node.id_] = node
            return node

        elif "trigger" in o:
            node = Trigger(**o)
            self.nodes[node.id_] = node
            return node

        elif "description" and "value" in o:
            return WorkflowVariable(**o)

        elif "actions" and "branches" in o:
            branches = {Branch(self.nodes[b.source], self.nodes[b.destination]) for b in self.branches}
            workflow_variables = {var.id_: var for var in o["workflow_variables"]}
            start = self.nodes[o["start"]]
            o["branches"] = branches
            o["workflow_variables"] = workflow_variables
            o["start"] = start
            return Workflow(**o)

        else:
            return o


class WorkflowJSONEncoder(json.JSONEncoder):
    """ A custom encoder for encoding Workflow types to JSON strings.
        Note: JSON encoded strings of our custom objects are lossy...for now.
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
            return {"id_": o.id_, "name": o.name, "app_name": o.app_name, "label": o.label, "position": o.position,
                    "parameters": o.parameters, "priority": o.priority, "execution_id": o.execution_id}

        elif isinstance(o, Condition):
            return {"id_": o.id_, "name": o.name, "app_name": o.app_name, "label": o.label, "position": o.position,
                    "conditional": o.conditional}

        elif isinstance(o, Transform):
            return {"id_": o.id_, "name": o.name, "app_name": o.app_name, "label": o.label, "position": o.position,
                    "transform": o.transform, "parameter": o.parameter}

        elif isinstance(o, Trigger):
            return {"id_": o.id_, "name": o.name, "app_name": o.app_name, "label": o.label, "position": o.position,
                    "trigger": o.trigger}

        elif isinstance(o, Parameter):
            return {"name": o.name, "variant": o.variant, "value": o.value, "reference": o.reference}

        elif isinstance(o, ParameterVariant):
            return o.value

        elif isinstance(o, WorkflowVariable):
            return {"description": o.description, "id_": o.id_, "name": o.name, "value": o.value}

        else:
            return o


Point = namedtuple("Point", ("x", "y"))
Branch = namedtuple("Branch", ("source", "destination"))
ParentSymbol = namedtuple("ParentSymbol", "result")  # used inside conditions to further mask the parent node attrs
ChildSymbol = namedtuple("ChildSymbol", "id_")  # used inside conditions to further mask the child node attrs


class ParameterVariant(enum.Enum):
    STATIC_VALUE = "STATIC_VALUE"
    ACTION_RESULT = "ACTION_RESULT"
    WORKFLOW_VARIABLE = "WORKFLOW_VARIABLE"
    GLOBAL = "GLOBAL"


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


class Node:
    def __init__(self, name, position: Point, label, app_name, id_=None):
        self.id_ = id_ if id_ is not None else str(uuid.uuid4())
        self.name = name
        self.app_name = app_name
        self.label = label
        self.position = position

    def __repr__(self):
        return f"Node-{self.id_}"

    def __str__(self):
        return f"Node-{self.label}"


class Action(Node):
    def __init__(self, name, position, app_name, label, priority, parameters=None, id_=None, execution_id=None):
        super().__init__(name, position, label, app_name, id_)
        self.parameters = parameters if parameters is not None else list()
        self.priority = priority
        self.execution_id = execution_id  # Only used by the app as a key for the redis queue

    def __str__(self):
        return f"Action: {self.label}::{self.id_}"

    def __repr__(self):
        return f"Action: {self.label}::{self.id_}"

    def __gt__(self, other):
        return self.priority > other.priority


class Condition(Node):
    def __init__(self, name, position: Point, app_name, label, conditional, id_=None):
        super().__init__(name, position, label, app_name, id_)
        self.conditional = conditional

    def __str__(self):
        return f"Condition: {self.label}::{self.id_}"

    def __repr__(self):
        return f"Condition: {self.label}::{self.id_}"

    @staticmethod
    def format_node_names(nodes):
        # We need to format space delimited names into underscore delimited names
        names_to_modify = {node.label for node in nodes.values() if node.label.count(' ') > 0}
        formatted_nodes = {}
        for node in nodes.values():
            formatted_name = node.label.strip().replace(' ', '_')

            if formatted_name in names_to_modify:  # we have to check for a name conflict as described above
                logger.error(f"Error processing condition. {node.label} or {formatted_name} must be renamed.")

            formatted_nodes[formatted_name] = node
        return formatted_nodes

    def __call__(self, parents, children, accumulator) -> str:
        parent_symbols = {k: ParentSymbol(accumulator[v.id_]) for k, v in self.format_node_names(parents).items()}
        children_symbols = {k: ChildSymbol(v.id_) for k, v in self.format_node_names(children).items()}
        syms = make_symbol_table(use_numpy=False, **parent_symbols, **children_symbols)
        aeval = Interpreter(usersyms=syms, no_for=True, no_while=True, no_try=True, no_functiondef=True, no_ifexp=True,
                            no_listcomp=True, no_augassign=True, no_assert=True, no_delete=True, no_raise=True,
                            no_print=True, use_numpy=False, builtins_readonly=True, readonly_symbols=children_symbols.keys())

        aeval(self.conditional)
        child_id = getattr(aeval.symtable.get("selected_node", None), "id_", None)

        if len(aeval.error) > 0:
            raise ConditionException

        return child_id


# TODO: fully realize and implement triggers
class Trigger(Node):
    def __init__(self, name, position: Point, app_name, label, trigger, id_=None):
        super().__init__(name, position, label, app_name, id_)
        self.trigger = trigger

    def __str__(self):
        return f"Trigger: {self.label}::{self.id_}"

    def __repr__(self):
        return f"Trigger: {self.label}::{self.id_}"


class Transform(Node):
    def __init__(self, name, position: Point, app_name, label, transform, parameter=None, id_=None):
        super().__init__(name, position, label, app_name, id_)
        self.transform = f"_{self.__class__.__name__}__{transform.lower()}"
        self.parameter = parameter

    def __call__(self, data):
        """ Execute an action and ship its result """
        logger.debug(f"Attempting execution of: {self.name}-{self.id_}")
        if hasattr(self, self.transform):
            if self.parameter is None:
                result = getattr(self, self.transform)(data=data)
            else:
                result = getattr(self, self.transform)(self.parameter, data=data)
            logger.debug(f"Executed {self.name}-{self.id_} with result: {result}")
            return result
        else:
            logger.error(f"{self.__class__.__name__} has no method {self.transform}")

    def __str__(self):
        return f"Transform: {self.label}::{self.id_}"

    def __repr__(self):
        return f"Transform: {self.label}::{self.id_}"

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
        self.start = start
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
