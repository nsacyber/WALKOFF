from flask import request
from flask_jwt_extended import jwt_required

from server.returncodes import *
from server.security import roles_accepted_for_resources


def send_data_to_trigger():
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('trigger')
    def __func():
        data = request.get_json()
        workflows_in = set(data['execution_uids'])
        data_in = data['data_in']
        arguments = data['arguments'] if 'arguments' in data else []

        workflows_awaiting_data = set(running_context.controller.get_waiting_workflows())
        print(workflows_awaiting_data)
        print(workflows_in)
        uids = set.intersection(workflows_in, workflows_awaiting_data)
        print(uids)

        running_context.controller.send_data_to_trigger(data_in, uids, arguments)
        return {}, SUCCESS

    return __func()

