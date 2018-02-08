from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims

from walkoff.coredb.argument import Argument
from walkoff.coredb.workflow import Workflow
from walkoff.coredb.saved_workflow import SavedWorkflow
from walkoff.server.returncodes import *
from walkoff.security import permissions_accepted_for_resources, ResourcePermissions
import walkoff.messaging
from walkoff.coredb import devicedb
from walkoff.events import WalkoffEvent


def send_data_to_trigger():
    from walkoff.server.context import running_context

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['execute']))
    def __func():
        data = request.get_json()
        workflows_in = set(data['execution_ids'])
        data_in = data['data_in']
        arguments = data['arguments'] if 'arguments' in data else []

        workflows_awaiting_data = set(running_context.controller.get_waiting_workflows())
        print(workflows_in)
        print(workflows_awaiting_data)
        execution_ids = set.intersection(workflows_in, workflows_awaiting_data)

        user_id = get_jwt_identity()
        authorization_not_required, authorized_execution_ids = get_authorized_execution_ids(
            execution_ids, user_id, get_jwt_claims().get('roles', []))
        add_user_in_progress(authorized_execution_ids, user_id)
        execution_ids = list(authorized_execution_ids | authorization_not_required)
        completed_execution_ids = []

        arg_objects = []
        for arg in arguments:
            arg_objects.append(Argument(**arg))

        for execution_id in execution_ids:
            saved_state = devicedb.device_db.session.query(SavedWorkflow).filter_by(workflow_execution_id=execution_id).first()
            workflow = devicedb.device_db.session.query(Workflow).filter_by(id=saved_state.workflow_id).first()
            workflow._execution_id = execution_id

            executed = False
            exec_action = None
            for action in workflow.actions:
                if action.id == saved_state.action_id:
                    exec_action = action
                    executed = action.execute_trigger(data_in, saved_state.accumulator)
                    break

            if executed:
                WalkoffEvent.TriggerActionTaken.send(exec_action, data={'workflow_execution_id': execution_id})
                completed_execution_ids.append(execution_id)
                running_context.controller.execute_workflow(workflow.id, start=saved_state.action_id,
                                                            start_arguments=arg_objects, resume=True)
            else:
                WalkoffEvent.TriggerActionNotTaken.send(exec_action, data={'workflow_execution_id': execution_id})

        return completed_execution_ids, SUCCESS

    return __func()


def get_authorized_execution_ids(execution_ids, user_id, role_ids):
    authorized_execution_ids = set()
    authorization_not_required = set()
    for execution_id in execution_ids:
        if not walkoff.messaging.workflow_authorization_cache.workflow_requires_authorization(execution_id):
            authorization_not_required.add(execution_id)
        elif any(walkoff.messaging.workflow_authorization_cache.is_authorized(execution_id, user_id, role_id)
                 for role_id in role_ids):
            authorized_execution_ids.add(execution_id)
    return authorization_not_required, authorized_execution_ids


def add_user_in_progress(execution_ids, user_id):
    for execution_id in execution_ids:
        walkoff.messaging.workflow_authorization_cache.add_user_in_progress(execution_id, user_id)
