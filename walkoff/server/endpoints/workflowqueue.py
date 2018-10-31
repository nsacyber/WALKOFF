from collections import OrderedDict

from flask import request, current_app
from flask_jwt_extended import jwt_required, get_jwt_claims
from sqlalchemy import exists

from walkoff.executiondb.argument import Argument
from walkoff.executiondb.workflow import Workflow
from walkoff.executiondb.workflowresults import WorkflowStatus, WorkflowStatusEnum
from walkoff.security import permissions_accepted_for_resources, ResourcePermissions
from walkoff.server.decorators import with_resource_factory, validate_resource_exists_factory, is_valid_uid
from walkoff.server.problem import Problem
from walkoff.server.returncodes import *
from walkoff.executiondb.environment_variable import EnvironmentVariable


def does_workflow_exist(workflow_id):
    return current_app.running_context.execution_db.session.query(exists().where(Workflow.id == workflow_id)).scalar()


def does_execution_id_exist(execution_id):
    return current_app.running_context.execution_db.session.query(
        exists().where(WorkflowStatus.execution_id == execution_id)).scalar()


def workflow_status_getter(execution_id):
    return current_app.running_context.execution_db.session.query(WorkflowStatus).filter_by(
        execution_id=execution_id).first()


def workflow_getter(workflow_id):
    return current_app.running_context.execution_db.session.query(Workflow).filter_by(id=workflow_id).first()


with_workflow = with_resource_factory('workflow', workflow_getter, validator=is_valid_uid)

with_workflow_status = with_resource_factory('workflow', workflow_status_getter, validator=is_valid_uid)
validate_workflow_is_registered = validate_resource_exists_factory('workflow', does_workflow_exist)
validate_execution_id_is_registered = validate_resource_exists_factory('workflow', does_execution_id_exist)

status_order = OrderedDict(
    [((WorkflowStatusEnum.running, WorkflowStatusEnum.awaiting_data, WorkflowStatusEnum.paused),
      WorkflowStatus.started_at),
     ((WorkflowStatusEnum.aborted, WorkflowStatusEnum.completed), WorkflowStatus.completed_at)])

executing_statuses = (WorkflowStatusEnum.running, WorkflowStatusEnum.awaiting_data, WorkflowStatusEnum.paused)
completed_statuses = (WorkflowStatusEnum.aborted, WorkflowStatusEnum.completed)


def get_all_workflow_status():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    def __func():
        page = request.args.get('page', 1, type=int)

        ret = current_app.running_context.execution_db.session.query(WorkflowStatus). \
            order_by(WorkflowStatus.status, WorkflowStatus.started_at.desc()). \
            limit(current_app.config['ITEMS_PER_PAGE']).\
            offset((page-1) * current_app.config['ITEMS_PER_PAGE'])

        ret = [workflow_status.as_json() for workflow_status in ret]
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
    data = request.get_json()
    workflow_id = data['workflow_id']

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['execute']))
    @with_workflow('execute', workflow_id)
    def __func(workflow):
        if not workflow.is_valid:
            return Problem(INVALID_INPUT_ERROR, 'Cannot execute workflow', 'Workflow is invalid')
        args = data['arguments'] if 'arguments' in data else None
        start = data['start'] if 'start' in data else None
        env_vars = data['environment_variables'] if 'environment_variables' in data else None

        env_var_objs = []
        if env_vars:
            env_var_objs = [EnvironmentVariable(**env_var) for env_var in env_vars]

        arguments = []
        if args:
            errors = []
            arguments = [Argument(**arg) for arg in args]
            for argument in arguments:
                if argument.errors:
                    errors.append('Errors in argument {}: {}'.format(argument.name, argument.errors))
            if errors:
                current_app.logger.error('Could not execute workflow. Invalid Argument construction')
                return Problem(
                    INVALID_INPUT_ERROR,
                    'Cannot execute workflow.',
                    'Some arguments are invalid. Reason: {}'.format(errors))

        execution_id = current_app.running_context.executor.execute_workflow(workflow_id, start=start,
                                                                             start_arguments=arguments,
                                                                             environment_variables=env_var_objs,
                                                                             user=get_jwt_claims().get('username', None))
        current_app.logger.info('Executed workflow {0}'.format(workflow_id))
        return {'id': execution_id}, SUCCESS_ASYNC

    return __func()


def control_workflow():
    data = request.get_json()
    execution_id = data['execution_id']

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['execute']))
    @validate_execution_id_is_registered('control', execution_id)
    def __func():
        status = data['status']

        if status == 'pause':
            current_app.running_context.executor.pause_workflow(execution_id,
                                                                user=get_jwt_claims().get('username', None))
        elif status == 'resume':
            current_app.running_context.executor.resume_workflow(execution_id,
                                                                 user=get_jwt_claims().get('username', None))
        elif status == 'abort':
            current_app.running_context.executor.abort_workflow(execution_id,
                                                                user=get_jwt_claims().get('username', None))

        return None, NO_CONTENT

    return __func()
