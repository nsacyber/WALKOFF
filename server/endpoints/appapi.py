from copy import deepcopy

from flask_jwt_extended import jwt_required

import core.config.config
import core.config.paths
from core import helpers
from server.returncodes import *
from server.security import roles_accepted_for_resources


def read_all_apps(interfaces_only=None):
    @jwt_required
    @roles_accepted_for_resources('apps')
    def __func():
        apps = helpers.list_apps_with_interfaces() if interfaces_only else helpers.list_apps()
        return sorted(apps, key=(lambda app_name: app_name.lower())), SUCCESS

    return __func()


def extract_schema(api, unformatted_fields=None):
    unformatted_fields = unformatted_fields if unformatted_fields is not None else ('name', 'example', 'description')
    ret = {}
    schema = {}
    for key, value in api.items():
        if key not in unformatted_fields:
            schema[key] = value
        else:
            ret[key] = value
    ret['schema'] = schema
    return ret


def format_returns(api, with_event=False):
    ret_returns = []
    for return_name, return_schema in api.items():
        return_schema.update({'status': return_name})
        ret_returns.append(return_schema)
    ret_returns.extend([{'status': 'UnhandledException', 'description': 'Exception occurred in action'},
                        {'status': 'InvalidInput', 'description': 'Input into the action was invalid'}])
    if with_event:
        ret_returns.append({'status': 'EventTimedOut', 'description': 'Action timed out out waiting for event'})
    return ret_returns


def format_app_action_api(api):
    ret = deepcopy(api)
    if 'returns' in api:
        ret['returns'] = format_returns(ret['returns'], 'event' in api)
    if 'parameters' in api:
        ret['parameters'] = [extract_schema(param_api) for param_api in ret['parameters']]
    else:
        ret['parameters'] = []
    return ret


def format_all_app_actions_api(api):
    actions = []
    for action_name, action_api in api.items():
        ret_action_api = {'name': action_name}
        ret_action_api.update(format_app_action_api(action_api))
        actions.append(ret_action_api)
    return actions


def format_device_api_full(api, device_name):
    device_api = {'name': device_name}
    unformatted_fields = ('name', 'description', 'default', 'encrypted', 'placeholder')
    if 'description' in api:
        device_api['description'] = api['description']
    device_api['fields'] = [extract_schema(device_field,
                                           unformatted_fields=unformatted_fields)
                            for device_field in api['fields']]

    return device_api


def format_full_app_api(api, app_name):
    ret = {'name': app_name}
    for unformatted_field in ('info', 'tags', 'externalDocs'):
        if unformatted_field in api:
            ret[unformatted_field] = api[unformatted_field]
        else:
            ret[unformatted_field] = [] if unformatted_field in ('tags', 'externalDocs') else {}
    for formatted_action_field in ('actions', 'conditions', 'transforms'):
        if formatted_action_field in api:
            ret[formatted_action_field[:-1] + '_apis'] = format_all_app_actions_api(api[formatted_action_field])
        else:
            ret[formatted_action_field[:-1] + '_apis'] = []
    if 'devices' in api:
        ret['device_apis'] = [format_device_api_full(device_api, device_name)
                              for device_name, device_api in api['devices'].items()]
    else:
        ret['device_apis'] = []
    return ret


@jwt_required
def read_all_app_apis(field_name=None):
    @roles_accepted_for_resources('apps')
    def __func():
        ret = []
        for app_name, app_api in core.config.config.app_apis.items():
            ret.append(format_full_app_api(app_api, app_name))
        if field_name is not None:
            default = [] if field_name not in ('info', 'externalDocs') else {}
            ret = [{'name': api['name'], field_name: api.get(field_name, default)} for api in ret]
        return ret, SUCCESS

    return __func()


@jwt_required
def read_app_api(app_name):
    @roles_accepted_for_resources('apps')
    def __func():
        api = core.config.config.app_apis.get(app_name, None)
        if api is not None:
            return format_full_app_api(api, app_name), SUCCESS
        else:
            return {'error': 'app not found'}, OBJECT_DNE_ERROR

    return __func()


@jwt_required
def read_app_api_field(app_name, field_name):
    @roles_accepted_for_resources('apps')
    def __func():
        api = core.config.config.app_apis.get(app_name, None)
        if api is not None:
            return format_full_app_api(api, app_name)[field_name], SUCCESS
        else:
            return {'error': 'app not found'}, OBJECT_DNE_ERROR

    return __func()
