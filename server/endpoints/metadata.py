import os

from flask import send_file
from flask_jwt_extended import jwt_required

import core.config.config
import core.config.paths
from core import helpers
from server.returncodes import SUCCESS
from server.security import roles_accepted_for_resources


def read_all_possible_subscriptions():

    @jwt_required
    @roles_accepted_for_resources('cases')
    def __func():
        return core.config.config.possible_events, SUCCESS

    return __func()


def read_all_transforms():

    @jwt_required
    @roles_accepted_for_resources('playbooks')
    def __func():
        transform_api = core.config.config.function_apis['transforms']
        transforms = {}
        for transform_name, transform_body in transform_api.items():
            ret = {}
            if 'description' in transform_body:
                ret['description'] = transform_body['description']
            data_in_param = transform_body['data_in']
            args = []
            for arg in (x for x in transform_body['parameters'] if x['name'] != data_in_param):
                arg_ret = {'name': arg['name'], 'type': arg.get('type', 'object')}
                if 'description' in arg:
                    arg_ret['description'] = arg['description']
                if 'required' in arg:
                    arg_ret['required'] = arg['required']
                args.append(arg)
            ret['args'] = args
            transforms[transform_name] = ret
        return {'transforms': transforms}, SUCCESS

    return __func()


def read_all_conditions():

    @jwt_required
    @roles_accepted_for_resources('playbooks')
    def __func():
        conditions_api = core.config.config.function_apis['conditions']
        conditions = {}
        for condition_name, condition_body in conditions_api.items():
            ret = {}
            if 'description' in condition_body:
                ret['description'] = condition_body['description']
            data_in_param = condition_body['data_in']
            args = []
            for arg in (x for x in condition_body['parameters'] if x['name'] != data_in_param):
                arg_ret = {'name': arg['name'], 'type': arg.get('type', 'object')}
                if 'description' in arg:
                    arg_ret['description'] = arg['description']
                if 'required' in arg:
                    arg_ret['required'] = arg['required']
                args.append(arg)
            ret['args'] = args
            conditions[condition_name] = ret
        return {"conditions": conditions}, SUCCESS

    return __func()


def read_all_device_types():
    @jwt_required
    @roles_accepted_for_resources('apps')
    def __func():
        response = []
        for app, app_api in core.config.config.app_apis.items():
            if 'devices' in app_api:
                for type_name, type_api in app_api['devices'].items():
                    api = dict(type_api)
                    api['name'] = type_name
                    api['app'] = app
                    response.append(api)
        return response, SUCCESS

    return __func()


def read_all_widgets():

    @jwt_required
    @roles_accepted_for_resources('apps')
    def __func():
        return {_app: helpers.list_widgets(_app) for _app in helpers.list_apps()}

    return __func()


def read_all_interfaces():

    @jwt_required
    @roles_accepted_for_resources('apps')
    def __func():
        return helpers.list_interfaces()


def validate_path(directory, filename):
    """ Checks that the filename is inside of the given directory
    Args:
        directory (str): The directory in which to search
        filename (str): The given filename

    Returns:
        (str): The sanitized path of the filename if valid, else None
    """
    base_abs_path = os.path.abspath(directory)
    normalized = os.path.normpath(os.path.join(base_abs_path, filename))
    return normalized if normalized.startswith(base_abs_path) else None


def read_client_file(filename):
    file = validate_path(core.config.paths.client_path, filename)
    if file is not None:
        return send_file(file), 200
    else:
        return {"error": "invalid path"}, 463
