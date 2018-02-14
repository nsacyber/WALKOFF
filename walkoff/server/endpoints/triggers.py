from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims

from walkoff.coredb.argument import Argument
from walkoff.server.returncodes import *
from walkoff.security import permissions_accepted_for_resources, ResourcePermissions
import walkoff.messaging


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
            if running_context.controller.resume_trigger_step(execution_id, data_in, arg_objects):
                completed_execution_ids.append(execution_id)

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
