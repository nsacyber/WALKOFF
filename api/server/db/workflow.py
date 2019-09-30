import logging
from uuid import uuid4, UUID
from typing import List

from pydantic import BaseModel, ValidationError, validator

from api.server.db.condition import ConditionModel
from api.server.db.transform import TransformModel
from api.server.db.branch import BranchModel
from api.server.db.workflow_variable import WorkflowVariableModel
from api.server.db.action import ActionModel
from api.server.db.trigger import TriggerModel
from api.server.db.permissions import PermissionsModel
from api.server.db import mongo

logger = logging.getLogger(__name__)


class WorkflowModel(BaseModel):
    id_: UUID
    errors: List[str] = []
    is_valid: bool = False  # self.error_check()
    name: str
    start: UUID
    description: str = ""
    tags: List[str] = []
    _walkoff_type: str = "workflow"
    permissions: PermissionsModel
    actions: List[ActionModel]
    branches: List[BranchModel] = []
    conditions: List[ConditionModel] = []
    transforms: List[TransformModel] = []
    workflow_variables: List[WorkflowVariableModel] = []
    triggers: List[TriggerModel] = []
    _secondary_id = "name"

    @classmethod
    @validator('start')
    def start_must_be_action(cls, start, workflow, **kwargs):
        if not any(start == action["id_"] for action in workflow["actions"]):
            raise ValidationError
        else:
            return start

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
    async def actions_must_exist(cls, actions, workflow, **kwargs):
        app_api_col = mongo.client.walkoff_db.apps
        ret = []
        for action in actions:
            action_api = await app_api_col.find({"name": action["app_name"], "actions.name": action["name"]})
            if not action_api:
                workflow.errors.append(f"Action {action.app_name}.{action.name} does not exist")
                continue
            else:
                ret += action
        return ret

    class Config:
        schema_extra = {
            'example': [
                {
                    "id_": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "name": "string",
                    "start": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "permissions": {
                        "access_level": 2,
                        "creator": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                        "role_permissions": [
                            {
                                "role": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                "permissions": [
                                    "read",
                                    "update",
                                    "delete"
                                ]
                            }
                        ]
                    },
                    "actions": [
                        {
                            "app_name": "hello_world",
                            "app_version": "1.0.0",
                            "name": "hello_world",
                            "label": "string",
                            "id_": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                            "errors": [
                                "string"
                            ],
                            "is_valid": True,
                            "position": {},
                            "priority": 0,
                            "parallelized": False,
                            "parameters": [
                                {
                                    "name": "string",
                                    "variant": "STATIC_VALUE",
                                    "id_": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                    "value": {},
                                    "parallelized": False
                                }
                            ]
                        }
                    ],
                    "errors": [
                        "string"
                    ],
                    "is_valid": False,
                    "description": "string",
                    "tags": [
                        "string"
                    ],
                    "branches": [
                        {
                            "source_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                            "destination_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                            "id_": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
                        }
                    ],
                    "conditions": [
                        {
                            "app_name": "string",
                            "app_version": "string",
                            "name": "string",
                            "label": "string",
                            "id_": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                            "errors": [
                                "string"
                            ],
                            "is_valid": True,
                            "position": {}
                        }
                    ],
                    "transforms": [
                        {
                            "app_name": "string",
                            "app_version": "string",
                            "name": "string",
                            "label": "string",
                            "id_": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                            "errors": [
                                "string"
                            ],
                            "is_valid": True,
                            "position": {}
                        }
                    ],
                    "workflow_variables": [
                        {
                            "name": "string",
                            "id_": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                            "description": "string"
                        }
                    ],
                    "triggers": [
                        {
                            "app_name": "string",
                            "app_version": "string",
                            "name": "string",
                            "label": "string",
                            "id_": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                            "errors": [
                                "string"
                            ],
                            "is_valid": True,
                            "position": {}
                        }
                    ]
                }
            ]
        }

    # @classmethod
    # @validator('actions')
    # def action_result_parameter_check(cls, actions, workflow, **kwargs):
    #     nodes = {node for node in workflow.actions + workflow.conditions
    #                 + workflow.transforms + workflow.triggers}
    #     ret = []
    #     for node in nodes:
    #         if node.parameters:
    #             for param in node.parameters:
    #
    #             else:
    #                 ret += action
    #     return ret
    #
    # @classmethod
    # @validator('actions')
    # def parallelized_actions_parameters_check(cls, actions, workflow, **kwargs):
    #     app_api_col = mongo.client.walkoff_db.apps
    #     ret = []
    #
    #     for action in actions:
    #         action_api = await app_api_col.find({"name": action["app_name"], "actions.name": action["name"]})
    #         params = {}
    #         for p in action_api.parameters:
    #             params[p.name] = {"api": p}
    #
    #         count = 0
    #         for p in action.parameters:
    #             params.get(p.name, {})["wf"] = p
    #             if p.parallelized:
    #                 count += 1
    #
    #         if count == 0 and action.parallelized:
    #             action.errors.append("No parallelized parameter set.")
    #         elif count == 1 and not action.parallelized:
    #             action.errors.append("Set action to be parallelized.")
    #         elif count > 1:
    #             action.errors.append("Too many parallelized parameters")
    #
    # @classmethod
    # @validator('actions')
    # def parameter_checking(cls, actions, workflow, **kwargs):
    #     app_api_col = mongo.client.walkoff_db.apps
    #     ret = []
    #
    #     for action in actions:
    #         action_api = await app_api_col.find({"name": action["app_name"], "actions.name": action["name"]})
    #         params = {}
    #         for p in action_api.parameters:
    #             params[p.name] = {"api": p}
    #
    #         for name, pair in params.items():
    #             api = pair.get("api")
    #             wf = pair.get("wf")
    #
    #             message = ""
    #
    #             if not api:
    #                 message = f"Parameter '{wf.name}' found in workflow but not in '{action.app_name}' API."
    #             elif not wf:
    #                 if api.required:
    #                     message = (f"Parameter '{api.name}' not found in workflow but is required in "
    #                                f"'{action.app_name}' API.")
    #             elif wf.variant == ParameterVariant.STATIC_VALUE:
    #                 try:
    #                     Draft4Validator(api.schema).validate(wf.value)
    #                 except JSONSchemaValidationError as e:
    #                     message = (f"Parameter {wf.name} value {wf.value} is not valid under given schema "
    #                                f"{api.schema}. JSONSchema output: {e}")
    #             elif wf.parallelized and not api.parallelizable:
    #                 action.errors.append(f"Parameter {wf.name} is marked parallelized in workflow, but is not "
    #                                      f"parallelizable in api")
    #
    #             if message is not "":
    #                 workflow.errors.append(message)

    def error_check(self):
        if self.errors:
            return False
        else:
            return True

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
