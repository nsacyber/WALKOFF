import uuid
from collections import namedtuple

from networkx import DiGraph


Point = namedtuple("Point", ("x", "y"))
Branch = namedtuple("Branch", ("src", "dst"))


class Node:
    def __init__(self, name, pos: Point):
        self.id = str(uuid.uuid4())
        self.name = name
        self.pos = pos

    def __repr__(self):
        return f"{self.name}"

    def __str__(self):
        return f"{self.name}"


class Action(Node):
    def __init__(self, display_name, action_name, app_name, params, priority, pos: Point):
        super().__init__(display_name, pos)
        self.execution_id = None
        self.app_name = app_name
        self.action_name = action_name
        self.params = params
        self.priority = priority

    def __gt__(self, other):
        return self.priority > other.priority

    def to_json(self):
        ret = {"execution_id": self.execution_id, "app_name": self.app_name, "action_name": self.action_name,
               "params": self.params, "name": self.name, "id": self.id, "pos": self.pos}
        return ret


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
    def __init__(self, name, start: Action, actions: [Action], branches: [Branch]):
        super().__init__()
        for branch in branches:
            self.add_edge(branch.src, branch.dst)
        self.add_nodes_from(actions)
        self.start = start
        self.id = str(uuid.uuid4())
        self.is_valid = self.validate()
        self.name = name

    def validate(self):
        return True

    @staticmethod
    def from_json(data):
        pass

    @staticmethod
    def to_json(data):
        pass
