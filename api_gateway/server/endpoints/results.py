from flask import current_app, request, jsonify
from flask_jwt_extended import jwt_required

from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, StatementError

from api_gateway.server.decorators import with_resource_factory, paginate, is_valid_uid
from api_gateway.executiondb.workflow import Workflow
from api_gateway.executiondb.workflowresults import WorkflowStatus, ActionStatus
from api_gateway.executiondb.schemas import WorkflowSchema, WorkflowStatusSchema, ActionStatusSchema

from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.problem import unique_constraint_problem, improper_json_problem, invalid_input_problem


def workflow_getter(workflow_id):
    return current_app.running_context.execution_db.session.query(Workflow).filter_by(id=workflow_id).first()


with_workflow = with_resource_factory('workflow', workflow_getter, validator=is_valid_uid)


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("workflowstatus", ["create"]))
@with_workflow('execute', 'workflow_id')
def create_workflow_status():
    pass


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("workflowstatus", ["create"]))
@with_workflow('execute', 'workflow_id')
def update_workflow_status():
    pass

