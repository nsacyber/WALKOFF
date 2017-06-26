import json
import os
from flask import render_template, current_app, send_file
from flask_security import login_required, current_user, roles_accepted
import core.config.config
import core.config.paths
import core.filters
import core.flags
from core import helpers
<<<<<<< HEAD
=======
from server.return_codes import SUCCESS, UNAUTHORIZED_ERROR

>>>>>>> upstream/development
from core.helpers import combine_dicts


def read_all_possible_subscriptions():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        return core.config.config.possible_events, SUCCESS

    return __func()


def read_all_filters():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/playbooks'])
    def __func():
        filter_api = core.config.config.function_apis['filters']
        filters = {}
        for filter_name, filter_body in filter_api.items():
            ret = {}
            if 'description' in filter_body:
                ret['description'] = filter_body['description']
            data_in_param = filter_body['dataIn']
            args = []
            for arg in (x for x in filter_body['parameters'] if x['name'] != data_in_param):
                arg_ret = {'name': arg['name'], 'type': arg.get('type', 'object')}
                if 'description' in arg:
                    arg_ret['description'] = arg['description']
                if 'required' in arg:
                    arg_ret['required'] = arg['required']
                args.append(arg)
            ret['args'] = args
            filters[filter_name] = ret
        return {'filters': filters}, SUCCESS

    return __func()


def read_all_flags():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/playbooks'])
    def __func():
        flag_api = core.config.config.function_apis['flags']
        flags = {}
        for flag_name, flag in flag_api.items():
            ret = {}
            if 'description' in flag:
                ret['description'] = flag['description']
            data_in_param = flag['dataIn']
            args = []
            for arg in (x for x in flag['parameters'] if x['name'] != data_in_param):
                arg_ret = {'name': arg['name'], 'type': arg.get('type', 'object')}
                if 'description' in arg:
                    arg_ret['description'] = arg['description']
                if 'required' in arg:
                    arg_ret['required'] = arg['required']
                args.append(arg)
            ret['args'] = args
            flags[flag_name] = ret
        return {"flags": flags}, SUCCESS

    return __func()


def sys_pages(interface_name):
    from server.context import running_context
    from server import interface

    @roles_accepted(*running_context.user_roles['/interface'])
    def __func():
        if current_user.is_authenticated and interface_name:
            args = getattr(interface, interface_name)()
            combine_dicts(args, {"authKey": current_user.get_auth_token()})
            return render_template("pages/" + interface_name + "/index.html", **args), SUCCESS
        else:
            current_app.logger.debug('Unsuccessful login attempt')
            return {"error": "Could not Log In."}, UNAUTHORIZED_ERROR

    return __func()


def login_info():
    @login_required
    def __func():
        if current_user.is_authenticated:
            return json.dumps({"auth_token": current_user.get_auth_token()}), SUCCESS
        else:
            current_app.logger.debug('Unsuccessful login attempt')
            return {"error": "Could not log in."}, UNAUTHORIZED_ERROR

    return __func()


def read_all_widgets():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/apps'])
    def __func():
        return {_app: helpers.list_widgets(_app) for _app in helpers.list_apps()}

    return __func()


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
