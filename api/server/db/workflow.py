import logging
from uuid import uuid4
from typing import List

from jsonschema import Draft4Validator, ValidationError as JSONSchemaValidationError
from pydantic import BaseModel, ValidationError, validator, UUID4

from common.workflow_types import ParameterVariant

from api.server.db.global_variable import GlobalVariable
from api.server.db.condition import ConditionModel
from api.server.db.transform import TransformModel
from api.server.db.branch import BranchModel
from api.server.db.workflow_variable import WorkflowVariableModel
from api.server.db import Base
from api.server.db.action import ActionModel
from api.server.db.trigger import TriggerModel
from api.server.db.permissions import PermissionsModel
from api.server.db import mongo

from common.helpers import validate_uuid


logger = logging.getLogger(__name__)


class WorkflowModel(BaseModel):
    id_: UUID4 = uuid4()
    errors: List[str] = []
    is_valid: bool = True
    name: str
    start: UUID4
    description: str = ""
    tags: str = ""
    _walkoff_type: str = "workflow"
    permissions: PermissionsModel
    actions = List[ActionModel]
    branches = List[BranchModel] = []
    conditions = List[ConditionModel] = []
    transforms = List[TransformModel] = []
    workflow_variables = List[WorkflowVariableModel] = []
    triggers = List[TriggerModel] = []

    @classmethod
    @validator('start')
    def start_must_be_action(cls, start, workflow, **kwargs):
        if not any(start == action["id_"] for action in workflow["actions"]):
            raise ValidationError

    @classmethod
    @validator('branches')
    def remove_invalid_branches(cls, branches, workflow, **kwargs):
        nodes = {node["id_"] for node
                 in workflow["actions"]
                 + workflow["conditions"]
                 + workflow["transforms"]
                 + workflow["triggers"]}

        return [branch for branch in branches
                if branch.source_id in nodes
                and branch.destination_id in nodes]

    @classmethod
    @validator('actions')
    def actions_must_exist(cls, actions, workflow, **kwargs):
        app_api_col = mongo.client.walkoff_db.apps
        for action in actions:
            app_api_col.find({"name": action["app_name"], "actions.name": action["name"]})


# class Workflow(Base):
#     __tablename__ = "workflow"
#
#     # Columns common to all DB models
#     id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)
#
#     # Columns common to validatable Workflow components
#     errors = Column(ARRAY(String))
#     is_valid = Column(Boolean, default=True)
#
#     name = Column(String(80), nullable=False, unique=True)
#     start = Column(UUID(as_uuid=True))
#     description = Column(String(), default="")
#     tags = Column(JSON, default="")
#     _walkoff_type = Column(String(80), default=__tablename__)
#     permissions = Column(JSON)
#     access_level = Column(Integer)
#     creator = Column(Integer, default=2)
#
#     actions = relationship("Action", cascade="all, delete-orphan", passive_deletes=True)
#     branches = relationship("Branch", cascade="all, delete-orphan", passive_deletes=True)
#     conditions = relationship("Condition", cascade="all, delete-orphan", passive_deletes=True)
#     transforms = relationship("Transform", cascade="all, delete-orphan", passive_deletes=True)
#     workflow_variables = relationship("WorkflowVariable", cascade="save-update")
#     triggers = relationship("Trigger", cascade="all, delete-orphan", passive_deletes=True)
#
#     children = ['actions', 'conditions', 'transforms', 'triggers']
#
#     def __init__(self, **kwargs):
#         super(Workflow, self).__init__(**kwargs)
#         self._walkoff_type = self.__tablename__
#         self.validate()
#
#     def validate(self):
#         """Validates the object"""
#         node_ids = {node.id_ for node in self.actions + self.conditions + self.transforms + self.triggers}
#         wfv_ids = {workflow_var.id_ for workflow_var in self.workflow_variables}
#         global_ids = set(id_ for id_, in current_app.running_context.execution_db.session.query(GlobalVariable.id_))
#
#         self.errors = []
#
#         if not self.start:
#             self.errors.append("Workflows must have a starting action.")
#         elif self.actions and self.start not in node_ids:
#             self.errors.append(f"Workflow start ID '{self.start}' not found in nodes")
#
#         self.branches[:] = [branch for branch in self.branches
#                             if branch.source_id in node_ids
#                             and branch.destination_id in node_ids]
#         action: Action
#         for action in self.actions:
#             errors = []
#
#             action_api = current_app.running_context.execution_db.session.query(ActionApi).filter(
#                 ActionApi.location == f"{action.app_name}.{action.name}"
#             ).first()
#
#             if not action_api:
#                 self.errors.append(f"Action {action.app_name}.{action.name} does not exist")
#                 continue
#
#             params = {}
#             for p in action_api.parameters:
#                 params[p.name] = {"api": p}
#
#             count = 0
#             for p in action.parameters:
#                 params.get(p.name, {})["wf"] = p
#                 if p.parallelized:
#                     count += 1
#
#             if count == 0 and action.parallelized:
#                 action.errors.append("No parallelized parameter set.")
#             elif count == 1 and not action.parallelized:
#                 action.errors.append("Set action to be parallelized.")
#             elif count > 1:
#                 action.errors.append("Too many parallelized parameters")
#
#             for name, pair in params.items():
#                 api = pair.get("api")
#                 wf = pair.get("wf")
#
#                 message = ""
#
#                 if not api:
#                     message = f"Parameter '{wf.name}' found in workflow but not in '{action.app_name}' API."
#                 elif not wf:
#                     if api.required:
#                         message = (f"Parameter '{api.name}' not found in workflow but is required in "
#                                    f"'{action.app_name}' API.")
#                 elif wf.variant == ParameterVariant.STATIC_VALUE:
#                     try:
#                         Draft4Validator(api.schema).validate(wf.value)
#                     except JSONSchemaValidationError as e:
#                         message = (f"Parameter {wf.name} value {wf.value} is not valid under given schema "
#                                    f"{api.schema}. JSONSchema output: {e}")
#                 elif wf.variant != ParameterVariant.STATIC_VALUE:
#                     wf_uuid = validate_uuid(wf.value)
#                     if not wf_uuid:
#                         message = (f"Parameter '{wf.name}' is a reference but '{wf.value}' is not a valid "
#                                    f"uuid4")
#                     elif wf.variant == ParameterVariant.ACTION_RESULT and wf_uuid not in node_ids:
#                         message = (f"Parameter '{wf.name}' refers to action '{wf.value}' "
#                                    f"which does not exist in this workflow.")
#                     elif wf.variant == ParameterVariant.WORKFLOW_VARIABLE and wf_uuid not in wfv_ids:
#                         message = (f"Parameter '{wf.name}' refers to workflow variable '{wf.value}' "
#                                    f"which does not exist in this workflow.")
#                     elif wf.variant == ParameterVariant.GLOBAL and wf_uuid not in global_ids:
#                         message = (f"Parameter '{wf.name}' refers to global variable '{wf.value}' "
#                                    f"which does not exist.")
#
#                 elif wf.parallelized and not api.parallelizable:
#                     action.errors.append(f"Parameter {wf.name} is marked parallelized in workflow, but is not "
#                                           f"parallelizable in api")
#
#                 if message is not "":
#                     errors.append(message)
#
#             action.errors = errors
#             action.is_valid = action.is_valid_rec()
#
#         self.is_valid = self.is_valid_rec()
#
#     def is_valid_rec(self):
#         if self.errors:
#             return False
#         for child in self.children:
#             child = getattr(self, child, None)
#             if isinstance(child, list):
#                 for actual_child in child:
#                     if not actual_child.is_valid_rec():
#                         return False
#             elif child is not None:
#                 if not child.is_valid_rec():
#                     return False
#         return True
#
#
# class WorkflowSchema(BaseSchema):
#     """Schema for workflows
#     """
#     actions = fields.Nested(ActionSchema, many=True)
#     branches = fields.Nested(BranchSchema, many=True)
#     conditions = fields.Nested(ConditionSchema, many=True)
#     transforms = fields.Nested(TransformSchema, many=True)
#     triggers = fields.Nested(TriggerSchema, many=True)
#     workflow_variables = fields.Nested(WorkflowVariableSchema, many=True)
#
#     class Meta:
#         model = Workflow
#         unknown = EXCLUDE
