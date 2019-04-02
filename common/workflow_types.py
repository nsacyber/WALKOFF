import uuid
import json
import enum
import logging
from operator import attrgetter, itemgetter
from collections import namedtuple, deque

from asteval import Interpreter, make_symbol_table

logger = logging.getLogger("WALKOFF")


def workflow_dumps(obj):
    return json.dumps(obj, cls=WorkflowJSONEncoder)


def workflow_loads(obj):
    return json.loads(obj, cls=WorkflowJSONDecoder)


def workflow_dump(obj, fp):
    return json.dump(obj, fp, cls=WorkflowJSONEncoder)


def workflow_load(obj, fp):
    return json.load(obj, fp, cls=WorkflowJSONDecoder)


def attrs_equal(self, other):
    attr_getters = (attrgetter(attr) for attr in self.__slots__)
    return all(attr_getter(self) == attr_getter(other) for attr_getter in attr_getters)


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

        elif "source_id" and "destination_id" in o:
            self.branches.add(Branch(source_id=o["source_id"], destination_id=o["destination_id"], id_=o["id_"]))

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
            branches = {Branch(self.nodes[b.source_id], self.nodes[b.destination_id], b.id_) for b in self.branches}
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
            # Unpack the adjacency matrix into edges
            branches = [{"source_id": src.id_, "destination_id": dst.id_} for src, dsts in o.edges.items()
                        for dst in dsts]
            branches.sort(key=itemgetter("source_id", "destination_id"))
            actions = [action for action in o.actions]
            conditions = [condition for condition in o.conditions]
            transforms = [transform for transform in o.transforms]
            triggers = [trigger for trigger in o.triggers]
            workflow_variables = list(o.workflow_variables.values())
            return {"id_": o.id_, "execution_id": o.execution_id, "name": o.name, "start": o.start.id_,
                    "actions": actions, "conditions": conditions, "branches": branches, "transforms": transforms,
                    "triggers": triggers, "workflow_variables": workflow_variables, "is_valid": o.is_valid,
                    "errors": None}

        elif isinstance(o, Action):
            position = {"x": o.position.x, "y": o.position.y, "id_": o.position.id_}
            return {"id_": o.id_, "name": o.name, "app_name": o.app_name, "app_version": o.app_version,
                    "label": o.label, "position": position, "parameters": o.parameters, "priority": o.priority,
                    "execution_id": o.execution_id}

        elif isinstance(o, Condition):
            position = {"x": o.position.x, "y": o.position.y, "id_": o.position.id_}
            return {"id_": o.id_, "name": o.name, "app_name": o.app_name, "label": o.label, "position": position,
                    "conditional": o.conditional}

        elif isinstance(o, Transform):
            position = {"x": o.position.x, "y": o.position.y, "id_": o.position.id_}
            return {"id_": o.id_, "name": o.name, "app_name": o.app_name, "label": o.label, "position": position,
                    "transform": o.transform, "parameter": o.parameter}

        elif isinstance(o, Trigger):
            position = {"x": o.position.x, "y": o.position.y, "id_": o.position.id_}
            return {"id_": o.id_, "name": o.name, "app_name": o.app_name, "label": o.label, "position": position,
                    "trigger": o.trigger}

        elif isinstance(o, Parameter):
            return {"name": o.name, "variant": o.variant, "value": o.value, "reference": o.reference, "id_": o.id_}

        elif isinstance(o, ParameterVariant):
            return o.value

        elif isinstance(o, WorkflowVariable):
            return {"description": o.description, "id_": o.id_, "name": o.name, "value": o.value}

        else:
            return o


Point = namedtuple("Point", ("x", "y", "id_"))
Branch = namedtuple("Branch", ("source_id", "destination_id", "id_"))
ParentSymbol = namedtuple("ParentSymbol", "result")  # used inside conditions to further mask the parent node attrs
ChildSymbol = namedtuple("ChildSymbol", "id_")  # used inside conditions to further mask the child node attrs


class ParameterVariant(enum.Enum):
    STATIC_VALUE = "STATIC_VALUE"
    ACTION_RESULT = "ACTION_RESULT"
    WORKFLOW_VARIABLE = "WORKFLOW_VARIABLE"
    GLOBAL = "GLOBAL"


class Parameter:
    __slots__ = ("name", "value", "variant", "reference", "id_", "errors")

    def __init__(self, name, id_=None, value=None, variant=None, reference=None, errors=None):
        self.id_ = id_
        self.name = name
        self.value = value
        self.variant: ParameterVariant = variant
        self.reference = reference
        self.errors = errors
        self.validate()

    def __str__(self):
        return f"Parameter-{self.name}:{self.value or self.reference}"

    def __eq__(self, other):
        if isinstance(other, Parameter) and self.__slots__ == other.__slots__:
            return attrs_equal(self, other)
        return False

    def __hash__(self):
        return hash(id(self))

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
    __slots__ = ("id_", "name", "value", "description")

    # Previously EnvironmentVariable
    def __init__(self, id_, name, value, description=None):
        self.id_ = id_
        self.name = name
        self.value = value
        self.description = description

    def __eq__(self, other):
        if isinstance(other, self.__class__) and self.__slots__ == other.__slots__:
            return attrs_equal(self, other)
        return False

    def __hash__(self):
        return hash(id(self))


class Node:
    __slots__ = ("id_", "name", "app_name", "label", "position", "priority", "errors")

    def __init__(self, name, position: Point, label, app_name, id_=None, errors=None):
        self.id_ = id_ if id_ is not None else str(uuid.uuid4())
        self.name = name
        self.app_name = app_name
        self.label = label
        self.position = position
        self.errors = errors if errors is not None else []
        if hasattr(self, "priority"):
            msg = f"Call super().__init__() prior to setting self.priority in Node subclass {self.__class__.__name__}"
            logger.warning(msg)
        else:
            self.priority = 3  # initialize this to mid level for non-Action node types

    def __repr__(self):
        return f"Node-{self.id_}"

    def __str__(self):
        return f"Node-{self.label}"

    def __gt__(self, other):
        return self.priority > other.priority

    def __eq__(self, other):
        if isinstance(other, self.__class__) and self.__slots__ == other.__slots__:
            return attrs_equal(self, other)
        return False

    def __hash__(self):
        return hash(id(self))


class Action(Node):
    __slots__ = ("parameters", "execution_id", "app_version")

    def __init__(self, name, position, app_name, app_version, label, priority, parameters=None, id_=None,
                 execution_id=None,
                 errors=None):
        super().__init__(name, position, label, app_name, id_, errors)
        self.app_version = app_version
        self.parameters = parameters if parameters is not None else list()
        self.priority = priority
        self.execution_id = execution_id  # Only used by the app as a key for the redis queue

    def __str__(self):
        return f"Action: {self.label}::{self.id_}"

    def __repr__(self):
        return f"Action: {self.label}::{self.id_}"

    def __eq__(self, other):
        if isinstance(other, self.__class__) and self.__slots__ == other.__slots__:
            return attrs_equal(self, other)
        return False

    def __hash__(self):
        return hash(id(self))


class Condition(Node):
    __slots__ = ("conditional",)

    def __init__(self, name, position: Point, app_name, label, conditional, id_=None, errors=None):
        super().__init__(name, position, label, app_name, id_, errors)
        self.conditional = conditional
        self.priority = 3  # Conditions have a fixed, mid valued priority

    def __str__(self):
        return f"Condition: {self.label}::{self.id_}"

    def __repr__(self):
        return f"Condition: {self.label}::{self.id_}"

    def __eq__(self, other):
        if isinstance(other, self.__class__) and self.__slots__ == other.__slots__:
            return attrs_equal(self, other)
        return False

    def __hash__(self):
        return hash(id(self))

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
                            no_print=True, use_numpy=False, builtins_readonly=True,
                            readonly_symbols=children_symbols.keys())

        aeval(self.conditional)
        child_id = getattr(aeval.symtable.get("selected_node", None), "id_", None)

        if len(aeval.error) > 0:
            raise ConditionException

        return child_id


# TODO: fully realize and implement triggers
class Trigger(Node):
    __slots__ = ("trigger",)

    def __init__(self, name, position: Point, app_name, label, trigger, id_=None, errors=None):
        super().__init__(name, position, label, app_name, id_, errors)
        self.trigger = trigger

    def __str__(self):
        return f"Trigger: {self.label}::{self.id_}"

    def __repr__(self):
        return f"Trigger: {self.label}::{self.id_}"

    def __eq__(self, other):
        if isinstance(other, self.__class__) and self.__slots__ == other.__slots__:
            return attrs_equal(self, other)
        return False

    def __hash__(self):
        return hash(id(self))


class Transform(Node):
    __slots__ = ("transform", "parameter")

    def __init__(self, name, position: Point, app_name, label, transform, parameter=None, id_=None, errors=None):
        super().__init__(name, position, label, app_name, id_, errors)
        self.transform = transform.lower()
        self.parameter = parameter
        self.priority = 3  # Transforms have a fixed, mid valued priority

    def __str__(self):
        return f"Transform: {self.label}::{self.id_}"

    def __repr__(self):
        return f"Transform: {self.label}::{self.id_}"

    def __eq__(self, other):
        if isinstance(other, self.__class__) and self.__slots__ == other.__slots__:
            return attrs_equal(self, other)
        return False

    def __hash__(self):
        return hash(id(self))

    def __call__(self, data):
        """ Execute an action and ship its result """
        logger.debug(f"Attempting execution of: {self.name}-{self.id_}")
        transform = f"_{self.__class__.__name__}__{self.transform}"
        if hasattr(self, transform):
            if self.parameter is None:
                result = getattr(self, transform)(data=data)
            else:
                result = getattr(self, transform)(self.parameter, data=data)
            logger.debug(f"Executed {self.name}-{self.id_} with result: {result}")
            return result
        else:
            logger.error(f"{self.__class__.__name__} has no method {self.transform}")

    # TODO: add JSON to CSV parsing and vice versa.
    def __get_value_at_index(self, index, data=None):
        return data[index]

    def __get_value_at_key(self, key, data=None):
        return data[key]

    def __split_string_to_array(self, delimiter=' ', data=None):
        return data.split(delimiter)


class DiGraph:
    __slots__ = ("nodes", "edges", "rev_adjacency")

    def __init__(self, nodes, edges):
        self.nodes = set()
        self.add_nodes(nodes)
        self.edges = {node: set() for node in self.nodes}
        self.rev_adjacency = {}  # all edges inverted for quickly getting parents of a node
        self.add_edges(edges)

    def __eq__(self, other):
        if isinstance(other, self.__class__) and self.__slots__ == other.__slots__:
            return attrs_equal(self, other)
        return False

    def __hash__(self):
        return hash(id(self))

    def add_edges(self, edges):
        try:
            iter(edges)  # check we got an iterable
            if callable(getattr(edges, "items", None)):  # check if it's a dictionary
                for src, dest in edges.items():
                    if src in self.edges:
                        self.edges[src].add(dest)
                    else:  # This edge introduces new nodes so lets add them
                        self.nodes.add(src)
                        self.nodes.add(dest)
                        self.edges[src] = {dest}
                    if dest in self.rev_adjacency:
                        self.edges[dest].add(src)
                    else:
                        self.edges[dest] = {src}
            else:  # it's a different iterable
                for edge in edges:
                    if not isinstance(edges, tuple) and not len(edge) == 2:
                        raise TypeError  # it must be an iterable of (src, dest) edges
                    src = edge[0]
                    dest = edge[1]
                    if src in self.edges:
                        self.edges[src].add(dest)
                    else:
                        self.edges[src] = {dest}

                    if dest in self.rev_adjacency:
                        self.rev_adjacency[dest].add(src)
                    else:
                        self.rev_adjacency[dest] = {src}
        except TypeError:
            return

    def add_edge(self, src, dest):
        self.add_edges({src, dest})

    def add_nodes(self, nodes):
        self.nodes = set(nodes)

    def add_node(self, node):
        return self.add_nodes([node])

    def successors(self, node):
        return self.edges[node]

    def predecessors(self, node):
        return self.rev_adjacency[node]


# TODO: Maybe look into pooling nodes/branches and sharing them across a workflow to save memory?
class Workflow(DiGraph):
    __slots__ = ("start", "id_", "is_valid", "name", "execution_id", "workflow_variables", "conditions", "transforms",
                 "triggers", "actions", "errors", "description", "tags")

    def __init__(self, name, start, actions: [Action], conditions: [Condition], triggers: [Trigger],
                 transforms: [Transform], branches: [Branch], workflow_variables, id_=None, execution_id=None,
                 is_valid=None, errors=None, description=None, tags=None):
        super().__init__(nodes=[*actions, *conditions, *triggers, *transforms], edges=branches)

        self.start = start
        self.id_ = id_ if id_ is not None else str(uuid.uuid4())
        self.is_valid = is_valid if is_valid is not None else self.validate()
        self.name = name
        self.execution_id = execution_id
        self.workflow_variables = workflow_variables if workflow_variables is not None else []
        self.conditions = conditions
        self.transforms = transforms
        self.triggers = triggers
        self.actions = actions
        self.errors = errors if errors is not None else []
        self.description = description
        self.tags = tags if tags is not None else []

    def __eq__(self, other):
        if isinstance(other, self.__class__) and self.__slots__ == other.__slots__:
            return attrs_equal(self, other)
        return False

    def __hash__(self):
        return hash(id(self))

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
