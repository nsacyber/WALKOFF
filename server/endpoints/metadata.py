import json
from flask import render_template
from flask_security import login_required, current_user, roles_accepted
import core.config.config
import core.config.paths
import core.filters
import core.flags
from core import helpers

from core.helpers import combine_dicts
from server import interface
from server import app

def display_possible_subscriptions():
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        return json.dumps(core.config.config.possible_events)
    return __func()


def get_apps():
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/apps'])
    def __func():
        return json.dumps({"apps": helpers.list_apps()})
    return __func()


def get_app_actions():
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/apps'])
    def __func():
        core.config.config.load_function_info()
        return json.dumps(core.config.config.function_info['apps'])
    return __func()


def get_filters():
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/playbooks'])
    def __func():
        return json.dumps({"status": "success", "filters": core.config.config.function_info['filters']})
    return __func()


def get_flags():
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/playbooks'])
    def __func():
        core.config.config.load_function_info()
        return json.dumps({"status": "success", "flags": core.config.config.function_info['flags']})
    return __func()


def sys_pages(interface_name):
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/interface'])
    def __func():
        if current_user.is_authenticated and interface_name:
            args = getattr(interface, interface_name)()
            combine_dicts(args, {"authKey": current_user.get_auth_token()})
            return render_template("pages/" + interface_name + "/index.html", **args)
        else:
            app.logger.debug('Unsuccessful login attempt')
            return {"status": "Could Not Log In."}
    return __func()


def login_info():
    @login_required
    def __func():
        if current_user.is_authenticated:
            return json.dumps({"auth_token": current_user.get_auth_token()})
        else:
            app.logger.debug('Unsuccessful login attempt')
            return {"status": "Could Not Log In."}
    return __func()


def get_widgets():
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/apps'])
    def __func():
        return json.dumps({_app: helpers.list_widgets(_app) for _app in helpers.list_apps()})
    return __func()
