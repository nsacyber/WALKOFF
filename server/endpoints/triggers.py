from flask import request
from flask_jwt_extended import jwt_required

from server.returncodes import *
from server.security import permissions_accepted_for_resources, ResourcePermissions


def send_data_to_trigger():
    from server.context import running_context

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['execute']))
    def __func():
        data = request.get_json()
        workflows_in = set(data['execution_uids'])
        data_in = data['data_in']
        arguments = data['arguments'] if 'arguments' in data else []

        workflows_awaiting_data = set(running_context.controller.get_waiting_workflows())
        uids = set.intersection(workflows_in, workflows_awaiting_data)

        running_context.controller.send_data_to_trigger(data_in, uids, arguments)
        return list(uids), SUCCESS

    return __func()
