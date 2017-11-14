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
        inputs = data['inputs'] if 'inputs' in data else {}

        workflows_awaiting_data = set(running_context.controller.get_waiting_workflows())
        uids = set.intersection(workflows_in, workflows_awaiting_data)

        running_context.controller.send_data_to_trigger(data_in, uids, inputs)
        return {}, SUCCESS

    return __func()

