import uuid
import json
from http import HTTPStatus
from datetime import datetime

from flask import current_app, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_claims

from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, StatementError

import jsonpatch

from api_gateway.server.decorators import with_resource_factory, paginate, is_valid_uid
from api_gateway.executiondb.workflow import Workflow
from api_gateway.executiondb.workflowresults import WorkflowStatus, ActionStatus
from api_gateway.executiondb.schemas import WorkflowSchema, WorkflowStatusSchema, ActionStatusSchema

from common.message_types import WorkflowStatusMessage
from common.message_types import ActionStatusMessage

from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.problem import unique_constraint_problem, improper_json_problem, invalid_input_problem


def workflow_getter(workflow_id):
    return current_app.running_context.execution_db.session.query(Workflow).filter_by(id_=workflow_id).first()


def workflow_status_getter(execution_id):
    return current_app.running_context.execution_db.session.query(WorkflowStatus).filter_by(execution_id=execution_id).first()


with_workflow = with_resource_factory('workflow', workflow_getter, validator=is_valid_uid)
with_workflow_status = with_resource_factory('workflow', workflow_status_getter, validator=is_valid_uid)

workflow_status_schema = WorkflowStatusSchema()


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("workflowstatus", ["create"]))
def create_workflow_status():
    workflow_status_json = request.get_json()
    workflow_id = workflow_status_json.get("workflow_id")
    workflow = workflow_getter(workflow_id)
    print(workflow_id)
    # if not workflow.is_valid:
    #     return invalid_input_problem("workflow", "execute", workflow.id_, errors=workflow.errors)

    execution_id = str(uuid.uuid4())

    workflow_status_json["status"] = "pending"
    workflow_status_json["name"] = workflow.name
    workflow_status_json["execution_id"] = execution_id

    try:
        workflow_status = workflow_status_schema.load(workflow_status_json)
        current_app.running_context.execution_db.session.add(workflow_status)
        current_app.running_context.execution_db.session.commit()
        current_app.logger.info(f"Created Workflow Status {workflow.name} ({execution_id})")
        return jsonify({'id': execution_id}), HTTPStatus.ACCEPTED
    except ValidationError as e:
        current_app.running_context.execution_db.session.rollback()
        return improper_json_problem('workflow_status', 'create', workflow.name, e.messages)
    except IntegrityError:
        current_app.running_context.execution_db.session.rollback()
        return unique_constraint_problem('workflow_status', 'create', workflow.name)


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("workflowstatus", ["create"]))
@with_workflow_status('update', 'execution_id')
def update_workflow_status(execution_id):
    old_workflow_status = workflow_status_schema.dump(execution_id)
    print(type(old_workflow_status))
    patch = jsonpatch.JsonPatch.from_string(json.dumps(request.get_json()))
    print(type(patch))
    new_workflow_status = patch.apply(old_workflow_status)
    print(type(new_workflow_status))

    try:
        workflow_status_schema.load(new_workflow_status, instance=execution_id)
        current_app.running_context.execution_db.session.commit()
        current_app.logger.info(f"Updated workflow status {execution_id.id_} ({execution_id.name})")
        return workflow_status_schema.dump(execution_id), HTTPStatus.OK
    except IntegrityError:
        current_app.running_context.execution_db.session.rollback()
        return unique_constraint_problem('workflow status', 'update', execution_id.id_)
