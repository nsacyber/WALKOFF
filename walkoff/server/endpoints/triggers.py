from flask import request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims

from walkoff.executiondb.argument import Argument
from walkoff.messaging.utils import log_action_taken_on_message
from walkoff.security import permissions_accepted_for_resources, ResourcePermissions
from walkoff.server.returncodes import *
from walkoff.serverdb.message import Message


def send_data_to_trigger():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['execute']))
    def __func():
        data = request.get_json()
        workflows_in = set(data['execution_ids'])
        data_in = data['data_in']
        arguments = data['arguments'] if 'arguments' in data else []

        workflows_awaiting_data = set(current_app.running_context.executor.get_waiting_workflows())
        execution_ids = set.intersection(workflows_in, workflows_awaiting_data)

        user_id = get_jwt_identity()
        authorization_not_required, authorized_execution_ids = get_authorized_execution_ids(
            execution_ids, user_id, get_jwt_claims().get('roles', []))
        execution_ids = list(authorized_execution_ids | authorization_not_required)
        completed_execution_ids = []

        arg_objects = []
        for arg in arguments:
            arg_objects.append(Argument(**arg))

        for execution_id in execution_ids:
            if current_app.running_context.executor.resume_trigger_step(execution_id, data_in, arg_objects,
                                                                        user=get_jwt_claims().get('username', None)):
                completed_execution_ids.append(execution_id)
                log_action_taken_on_message(user_id, execution_id)

        return completed_execution_ids, SUCCESS

    return __func()


def get_authorized_execution_ids(execution_ids, user_id, role_ids):
    authorized_execution_ids = set()
    authorization_not_required = set()
    for execution_id in execution_ids:
        message = Message.query.filter(Message.workflow_execution_id == execution_id).first()
        if not (message and message.requires_response):
            authorization_not_required.add(execution_id)
        elif message.requires_response and message.is_authorized(user_id, role_ids):
            authorized_execution_ids.add(execution_id)
    return authorization_not_required, authorized_execution_ids
