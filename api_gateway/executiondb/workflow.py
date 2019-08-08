import logging
from uuid import uuid4

from sqlalchemy import Column, String, Boolean, JSON, event
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from marshmallow import fields, EXCLUDE
from jsonschema import Draft4Validator, ValidationError as JSONSchemaValidationError

from flask import current_app

from common.workflow_types import ParameterVariant

from api_gateway.helpers import validate_uuid
from api_gateway.executiondb.global_variable import GlobalVariable
from api_gateway.executiondb.condition import ConditionSchema
from api_gateway.executiondb.transform import TransformSchema
from api_gateway.executiondb.branch import BranchSchema
from api_gateway.executiondb.workflow_variable import WorkflowVariableSchema
from api_gateway.executiondb import Base, BaseSchema
from api_gateway.executiondb.action import ActionSchema, ActionApi, Action
from api_gateway.executiondb.trigger import TriggerSchema

logger = logging.getLogger(__name__)


class Workflow(Base):
    __tablename__ = "workflow"

    # Columns common to all DB models
    id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)

    # Columns common to validatable Workflow components
    errors = Column(ARRAY(String))
    is_valid = Column(Boolean, default=True)

    name = Column(String(80), nullable=False, unique=True)
    start = Column(UUID(as_uuid=True))
    description = Column(String(), default="")
    tags = Column(JSON, default="")
    _walkoff_type = Column(String(80), default=__tablename__)
    permissions = Column(JSON)

    actions = relationship("Action", cascade="all, delete-orphan", passive_deletes=True)
    branches = relationship("Branch", cascade="all, delete-orphan", passive_deletes=True)
    conditions = relationship("Condition", cascade="all, delete-orphan", passive_deletes=True)
    transforms = relationship("Transform", cascade="all, delete-orphan", passive_deletes=True)
    workflow_variables = relationship("WorkflowVariable", cascade="save-update")
    triggers = relationship("Trigger", cascade="all, delete-orphan", passive_deletes=True)

    children = ['actions', 'conditions', 'transforms', 'triggers']

    def __init__(self, **kwargs):
        super(Workflow, self).__init__(**kwargs)
        self._walkoff_type = self.__tablename__
        self.validate()

    def validate(self):
        """Validates the object"""
        node_ids = {node.id_ for node in self.actions + self.conditions + self.transforms + self.triggers}
        wfv_ids = {workflow_var.id_ for workflow_var in self.workflow_variables}
        global_ids = set(id_ for id_, in current_app.running_context.execution_db.session.query(GlobalVariable.id_))

        self.errors = []

        if not self.start:
            self.errors.append("Workflows must have a starting action.")
        elif self.actions and self.start not in node_ids:
            self.errors.append(f"Workflow start ID '{self.start}' not found in nodes")

        self.branches[:] = [branch for branch in self.branches
                            if branch.source_id in node_ids
                            and branch.destination_id in node_ids]
        action: Action
        for action in self.actions:
            errors = []

            action_api = current_app.running_context.execution_db.session.query(ActionApi).filter(
                ActionApi.location == f"{action.app_name}.{action.name}"
            ).first()

            if not action_api:
                self.errors.append(f"Action {action.app_name}.{action.name} does not exist")
                continue

            params = {}
            for p in action_api.parameters:
                params[p.name] = {"api": p}

            count = 0
            for p in action.parameters:
                params.get(p.name, {})["wf"] = p
                if p.parallelized:
                    count += 1

            if count == 0 and action.parallelized:
                action.errors.append("No parallelized parameter set.")
            elif count == 1 and not action.parallelized:
                action.errors.append("Set action to be parallelized.")
            elif count > 1:
                action.errors.append("Too many parallelized parameters")

            for name, pair in params.items():
                api = pair.get("api")
                wf = pair.get("wf")

                message = ""

                if not api:
                    message = f"Parameter '{wf.name}' found in workflow but not in '{action.app_name}' API."
                elif not wf:
                    if api.required:
                        message = (f"Parameter '{api.name}' not found in workflow but is required in "
                                   f"'{action.app_name}' API.")
                elif wf.variant == ParameterVariant.STATIC_VALUE:
                    try:
                        Draft4Validator(api.schema).validate(wf.value)
                    except JSONSchemaValidationError as e:
                        message = (f"Parameter {wf.name} value {wf.value} is not valid under given schema "
                                   f"{api.schema}. JSONSchema output: {e}")
                elif wf.variant != ParameterVariant.STATIC_VALUE:
                    wf_uuid = validate_uuid(wf.value)
                    if not wf_uuid:
                        message = (f"Parameter '{wf.name}' is a reference but '{wf.value}' is not a valid "
                                   f"uuid4")
                    elif wf.variant == ParameterVariant.ACTION_RESULT and wf_uuid not in node_ids:
                        message = (f"Parameter '{wf.name}' refers to action '{wf.value}' "
                                   f"which does not exist in this workflow.")
                    elif wf.variant == ParameterVariant.WORKFLOW_VARIABLE and wf_uuid not in wfv_ids:
                        message = (f"Parameter '{wf.name}' refers to workflow variable '{wf.value}' "
                                   f"which does not exist in this workflow.")
                    elif wf.variant == ParameterVariant.GLOBAL and wf_uuid not in global_ids:
                        message = (f"Parameter '{wf.name}' refers to global variable '{wf.value}' "
                                   f"which does not exist.")

                elif wf.parallelized and not api.parallelizable:
                    action.errors.append(f"Parameter {wf.name} is marked parallelized in workflow, but is not "
                                          f"parallelizable in api")

                if message is not "":
                    errors.append(message)

            action.errors = errors
            action.is_valid = action.is_valid_rec()

        self.is_valid = self.is_valid_rec()

    def is_valid_rec(self):
        if self.errors:
            return False
        for child in self.children:
            child = getattr(self, child, None)
            if isinstance(child, list):
                for actual_child in child:
                    if not actual_child.is_valid_rec():
                        return False
            elif child is not None:
                if not child.is_valid_rec():
                    return False
        return True


class WorkflowSchema(BaseSchema):
    """Schema for workflows
    """
    actions = fields.Nested(ActionSchema, many=True)
    branches = fields.Nested(BranchSchema, many=True)
    conditions = fields.Nested(ConditionSchema, many=True)
    transforms = fields.Nested(TransformSchema, many=True)
    triggers = fields.Nested(TriggerSchema, many=True)
    workflow_variables = fields.Nested(WorkflowVariableSchema, many=True)

    class Meta:
        model = Workflow
        unknown = EXCLUDE
