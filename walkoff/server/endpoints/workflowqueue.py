from uuid import UUID
from flask import request, current_app
from flask_jwt_extended import jwt_required
from sqlalchemy import exists
import walkoff.config.paths
from walkoff.coredb.workflowresults import WorkflowStatus
from walkoff.server.returncodes import *
from walkoff.security import permissions_accepted_for_resources, ResourcePermissions
from walkoff.server.decorators import with_resource_factory, validate_resource_exists_factory
import walkoff.coredb.devicedb
from walkoff.coredb.workflow import Workflow
from walkoff.coredb.argument import Argument
from walkoff.helpers import InvalidArgument


def does_workflow_exist(workflow_id):
    return walkoff.coredb.devicedb.device_db.session.query(
        exists().where(Workflow.id == workflow_id)).scalar()


def does_execution_id_exist(execution_id):
    return walkoff.coredb.devicedb.device_db.session.query(exists().where(WorkflowStatus.execution_id == execution_id)).scalar()


def workflow_status_getter(execution_id):
    return walkoff.coredb.devicedb.device_db.session.query(WorkflowStatus).filter_by(execution_id=execution_id).first()


def is_valid_uid(*ids):
    try:
        for id_ in ids:
            UUID(id_)
        return True
    except ValueError:
        return False


with_workflow_status = with_resource_factory('workflow', workflow_status_getter, validator=is_valid_uid)
validate_workflow_is_registered = validate_resource_exists_factory('workflow', does_workflow_exist)
validate_execution_id_is_registered = validate_resource_exists_factory('workflow', does_execution_id_exist)


def get_all_workflow_status():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    def __func():
        workflow_statuses = walkoff.coredb.devicedb.device_db.session.query(WorkflowStatus).all()
        ret = [workflow_status.as_json() for workflow_status in workflow_statuses]
        return ret, SUCCESS

    return __func()


def get_workflow_status(execution_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    @with_workflow_status('control', execution_id)
    def __func(workflow_status):
        return workflow_status.as_json(full_actions=True), SUCCESS

    return __func()


def execute_workflow():
    from walkoff.server.context import running_context

    data = request.get_json()
    workflow_id = data['workflow_id']

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['execute']))
    @validate_workflow_is_registered('execute', workflow_id)
    def __func():
        args = data['arguments'] if 'arguments' in data else None
        start = data['start'] if 'start' in data else None

        arguments = []
        if args:
            for arg in args:
                try:
                    arguments.append(Argument(**arg))
                except InvalidArgument:
                    current_app.logger.error('Could not execute workflow. Invalid Argument construction')
                    return {"error": "Could not execute workflow. Invalid argument construction"}, INVALID_INPUT_ERROR

        execution_id = running_context.controller.execute_workflow(workflow_id, start=start, start_arguments=arguments)
        current_app.logger.info('Executed workflow {0}'.format(workflow_id))
        return {'id': execution_id}, SUCCESS_ASYNC

    return __func()


def control_workflow():
    from walkoff.server.context import running_context

    data = request.get_json()
    execution_id = data['execution_id']

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['execute']))
    @validate_execution_id_is_registered('control', execution_id)
    def __func():
        status = data['status']

        if status == 'pause':
            running_context.controller.pause_workflow(execution_id)
        elif status == 'resume':
            running_context.controller.resume_workflow(execution_id)
        elif status == 'abort':
            running_context.controller.abort_workflow(execution_id)

        return {}, SUCCESS

    return __func()
