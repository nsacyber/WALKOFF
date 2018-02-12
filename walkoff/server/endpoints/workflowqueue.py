import json
from uuid import UUID
from flask import request, current_app
from flask_jwt_extended import jwt_required
from sqlalchemy import exists
import walkoff.case.database as case_database
import walkoff.config.paths
from walkoff.coredb.workflowresults import WorkflowStatus
from walkoff.server.returncodes import *
from walkoff.security import permissions_accepted_for_resources, ResourcePermissions
from walkoff.server.decorators import with_resource_factory, validate_resource_exists_factory
import walkoff.coredb.devicedb
from walkoff.coredb import WorkflowStatusEnum
from walkoff.coredb.workflow import Workflow
from walkoff.coredb.argument import Argument
from walkoff.helpers import InvalidArgument


def does_workflow_exist(workflow_id):
    return walkoff.coredb.devicedb.device_db.session.query(
        exists().where(Workflow.id == workflow_id)).scalar()


def workflow_getter(workflow_id):
    return walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(id=workflow_id).first()


def is_valid_uid(*ids):
    try:
        for id_ in ids:
            UUID(id_)
        return True
    except ValueError:
        return False


with_workflow = with_resource_factory('workflow', workflow_getter, validator=is_valid_uid)
validate_workflow_is_registered = validate_resource_exists_factory('workflow', does_workflow_exist)


def execute_workflow(workflow_id):
    from walkoff.server.context import running_context

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['execute']))
    @validate_workflow_is_registered('execute', workflow_id)
    def __func():
        data = request.get_json()
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
        current_app.logger.info('Executed workflow {0}-{1}'.format(playbook_id, workflow_id))
        return {'id': execution_id}, SUCCESS_ASYNC

    return __func()


def pause_workflow(execution_id):
    from walkoff.server.context import running_context

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['execute']))
    @validate_workflow_is_registered('pause', playbook_id, workflow_id)
    def __func():
        data = request.get_json()
        execution_id = data['id']
        status = running_context.controller.executor.get_workflow_status(execution_id)
        if status == WorkflowStatusEnum.running:  # WORKFLOW_RUNNING
            running_context.controller.pause_workflow(execution_id)
            current_app.logger.info(
                'Paused workflow {0}-{1}:{2}'.format(playbook_id, workflow_id, execution_id))
            return {"info": "Workflow paused"}, SUCCESS
        elif status == WorkflowStatusEnum.paused:
            return {"info": "Workflow already paused"}, SUCCESS
        elif status == 0:
            return {"error": 'Invalid UUID'}, INVALID_INPUT_ERROR
        else:
            return {"error": 'Workflow not in running state'}, SUCCESS_WITH_WARNING

    return __func()


def resume_workflow(execution_id):
    from walkoff.server.context import running_context

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['execute']))
    @validate_workflow_is_registered('resume', playbook_id, workflow_id)
    def __func():
        data = request.get_json()
        execution_id = data['id']
        status = running_context.controller.executor.get_workflow_status(execution_id)
        if status == WorkflowStatusEnum.paused:  # WORKFLOW_PAUSED
            running_context.controller.resume_workflow(execution_id)
            current_app.logger.info(
                'Resumed workflow {0}-{1}:{2}'.format(playbook_id, workflow_id, execution_id))
            return {"info": "Workflow resumed"}, SUCCESS
        elif status == WorkflowStatusEnum.running:
            return {"info": "Workflow already running"}, SUCCESS
        elif status == 0:
            return {"error": 'Invalid UUID'}, INVALID_INPUT_ERROR
        else:
            return {"error": 'Workflow not in paused state'}

    return __func()


@jwt_required
def read_results():
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    def __func():
        ret = []
        completed_workflows = [workflow.as_json() for workflow in
                               case_database.case_db.session.query(WorkflowStatus).filter(
                                   WorkflowStatus.status == 'completed').all()]
        for result in completed_workflows:
            if result['status'] == 'completed':
                ret.append({'name': result['name'],
                            'timestamp': result['completed_at'],
                            'result': json.dumps(result['results'])})
        return ret, SUCCESS

    return __func()


def read_all_results():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    def __func():
        return [workflow.as_json() for workflow in
                case_database.case_db.session.query(WorkflowStatus).all()], SUCCESS

    return __func()


def read_result(execution_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    def __func():
        workflow_result = case_database.case_db.session.query(WorkflowStatus).filter(
            WorkflowStatus.execution_id == execution_id).first()
        if workflow_result is not None:
            return workflow_result.as_json(), SUCCESS
        else:
            return {'error': 'No workflow found'}, OBJECT_DNE_ERROR

    return __func()
