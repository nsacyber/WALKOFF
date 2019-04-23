import logging
import uuid

from sqlalchemy import Column, String, JSON, event
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType
from marshmallow import fields, EXCLUDE
from marshmallow_sqlalchemy import field_for
from jsonschema import Draft4Validator, ValidationError as JSONSchemaValidationError

from flask import current_app

from common.workflow_types import ParameterVariant

from api_gateway.helpers import validate_uuid4
from api_gateway.executiondb.global_variable import GlobalVariable
from api_gateway.executiondb.condition import ConditionSchema
from api_gateway.executiondb.transform import TransformSchema
from api_gateway.executiondb.branch import BranchSchema
from api_gateway.executiondb.workflow_variable import WorkflowVariableSchema
from api_gateway.executiondb import Base, ValidatableMixin, BaseSchema
from api_gateway.executiondb.action import Action, ActionSchema, ActionApi
from api_gateway.executiondb.trigger import TriggerSchema

logger = logging.getLogger(__name__)


class Workflow(ValidatableMixin, Base):
    __tablename__ = "workflow"
    name = Column(String(80), nullable=False, unique=True)
    start = Column(UUIDType(binary=False))
    description = Column(String(), default="")
    tags = Column(JSON, default="")

    actions = relationship("Action", cascade="all, delete-orphan", passive_deletes=True)
    branches = relationship("Branch", cascade="all, delete-orphan", passive_deletes=True)
    conditions = relationship("Condition", cascade="all, delete-orphan", passive_deletes=True)
    transforms = relationship("Transform", cascade="all, delete-orphan", passive_deletes=True)
    workflow_variables = relationship("WorkflowVariable", cascade="all, delete-orphan", passive_deletes=True)
    triggers = relationship("Trigger", cascade="all, delete-orphan", passive_deletes=True)

    def __init__(self, **kwargs):
        super(Workflow, self).__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validates the object"""
        node_ids = {node.id_ for node in self.actions + self.conditions + self.transforms}
        work_var_ids = {workflow_var.id_ for workflow_var in self.workflow_variables}
        global_ids = set(current_app.running_context.execution_db.session.query(GlobalVariable.id_).all())
        errors = []
        if not self.start and self.actions:
            errors.append("Workflows must have a starting action.")
        elif self.actions and self.start not in node_ids:
            errors.append(f"Workflow start ID {self.start} not found in nodes")
        for branch in self.branches:
            # Todo: Should these just be removed?
            if branch.source_id not in node_ids:
                errors.append(f"Branch source ID {branch.source_id} not found in nodes")
            if branch.destination_id not in node_ids:
                errors.append(f"Branch destination ID {branch.destination_id} not found in nodes")

        for action in self.actions:
            action_api = current_app.running_context.execution_db.session.query(ActionApi).filter(
                ActionApi.location == f"{action.app_name}.{action.name}"
            ).first()
            params = {}
            for p in action_api.parameters:
                params[p.name] = {"api": p}

            for p in action.parameters:
                params.get(p.name, {})["wf"] = p

            for name, pair in params.items():
                api = pair.get("api")
                wf = pair.get("wf")

                if not api:
                    errors.append(f"Parameter {wf.name} found in workflow but not in {action.app_name} API spec.")

                if wf.variant != ParameterVariant.STATIC_VALUE:
                    if not validate_uuid4(wf.value):
                        errors.append(f"Parameter {wf.name} is a reference but {wf.value} is not a valid uuid4")
                    elif uuid.UUID(wf.value) not in node_ids.union(work_var_ids, global_ids):
                        errors.append(f"Parameter {wf.name} refers to {wf.value} not found in {wf.variant}.")
                else:
                    try:
                        Draft4Validator(api.schema).validate(wf.value)
                    except JSONSchemaValidationError as e:
                        errors.append(f"Parameter {wf.name} value {wf.value} not valid under schema {api.schema}.")

        self.errors = errors
        self.is_valid = not bool(errors)


@event.listens_for(Workflow, "before_update")
def validate_before_update(mapper, connection, target):
    target.validate()


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
