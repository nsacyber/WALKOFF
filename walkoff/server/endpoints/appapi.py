from copy import deepcopy

from flask_jwt_extended import jwt_required

import walkoff.config
from walkoff import helpers
from walkoff.appgateway import is_app_action_bound
from walkoff.definitions import ReturnApi
from walkoff.security import permissions_accepted_for_resources, ResourcePermissions
from walkoff.server.problem import Problem
from walkoff.server.returncodes import *


def read_all_apps():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('app_apis', ['read']))
    def __func():
        apps = helpers.list_apps(walkoff.config.Config.APPS_PATH)
        return sorted(apps, key=(lambda app_name: app_name.lower())), SUCCESS

    return __func()


def extract_schema(api, unformatted_fields=('name', 'example', 'placeholder', 'description', 'required')):
    api = api.__dict__
    ret = {}
    schema = {}
    for key, value in api.items():
        if key in unformatted_fields:
            ret[key] = value
        else:
            schema[key] = value
    ret['schema'] = schema
    while 'schema' in ret['schema']:  # flatten the nested schema, happens when parameter is an object
        ret['schema'].update(ret['schema'].pop('schema').__dict__)
    return ret


def format_returns(api, with_event=False):
    ret_returns = []
    for return_name, return_schema in api.items():
        return_schema.status = return_name
        ret_returns.append(return_schema)
    ret_returns.extend(
        [ReturnApi({'status': 'UnhandledException', 'failure': True, 'description': 'Exception occurred in action'}),
        ReturnApi({'status': 'InvalidInput', 'failure': True, 'description': 'Input into the action was invalid'})])
    if with_event:
        ret_returns.append(ReturnApi(
            {'status': 'EventTimedOut', 'failure': True, 'description': 'Action timed out out waiting for event'}))
    return ret_returns


def format_app_action_api(api, app_name, action_type):
    ret = deepcopy(api)
    ret.returns = format_returns(ret.returns)  #, hasattr(api, 'event')
    ret.parameters = [extract_schema(param_api) for param_api in ret.parameters]
    ret = ret.__dict__
    if action_type in ('conditions', 'transforms') or not is_app_action_bound(app_name, api.run):
        ret['global'] = True
    return ret


def format_all_app_actions_api(api, app_name, action_type):
    actions = []
    for action_name, action_api in api.items():
        ret_action_api = {'name': action_name}
        ret_action_api.update(format_app_action_api(action_api, app_name, action_type))
        actions.append(ret_action_api)
    return sorted(actions, key=lambda action: action['name'])


def format_device_api_full(api, device_name):
    device_api = {'name': device_name}
    unformatted_fields = ('name', 'description', 'encrypted', 'placeholder', 'required')
    if hasattr(api, 'description'):
        device_api['description'] = api.description
    device_api['fields'] = [extract_schema(device_field,
                                           unformatted_fields=unformatted_fields)
                            for device_field in api.fields]

    return device_api


def format_full_app_api(api, app_name):
    ret = {'name': app_name}
    for unformatted_field in ('info', 'tags', 'external_docs'):
        if hasattr(api, unformatted_field):
            ret[unformatted_field] = getattr(api, unformatted_field)
        else:
            ret[unformatted_field] = [] if unformatted_field in ('tags', 'external_docs') else {}
    for formatted_action_field in ('actions', 'conditions', 'transforms'):
        ret[formatted_action_field[:-1] + '_apis'] = format_all_app_actions_api(getattr(api, formatted_action_field),
                                                                                app_name, formatted_action_field)
    ret['device_apis'] = [format_device_api_full(device_api, device_name)
                          for device_name, device_api in api.devices.items()]
    return ret


def read_all_app_apis(field_name=None):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('app_apis', ['read']))
    def __func():
        ret = []
        for app_name, app_api in walkoff.config.app_apis.items():
            ret.append(format_full_app_api(app_api, app_name))
        if field_name is not None:
            default = [] if field_name not in ('info', 'external_docs') else {}
            ret = [{'name': api['name'], field_name: api.get(field_name, default)} for api in ret]
        return ret, SUCCESS

    return __func()


def app_api_dne_problem(app_name):
    return Problem(OBJECT_DNE_ERROR, 'Could not read app api.', 'App {} does not exist.'.format(app_name))


def read_app_api(app_name):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('app_apis', ['read']))
    def __func():
        api = walkoff.config.app_apis.get(app_name, None)
        if api is not None:
            return format_full_app_api(api, app_name), SUCCESS
        else:
            return app_api_dne_problem(app_name)

    return __func()


@jwt_required
def read_app_api_field(app_name, field_name):
    @permissions_accepted_for_resources(ResourcePermissions('app_apis', ['read']))
    def __func():
        api = walkoff.config.app_apis.get(app_name, None)
        if api is not None:
            return format_full_app_api(api, app_name)[field_name], SUCCESS
        else:
            return app_api_dne_problem(app_name)

    return __func()
