import json

from flask import current_app

def get_app_action_api(app_name, action_name):
    """
    Gets the api for a given app and action

    Args:
        app (str): Name of the app
        action (str): Name of the action

    Returns:
        (tuple(str, dict)) The name of the function to execute and its parameters
    """
    try:
        app_api = current_app.running_context.app_cache[app_name]
        if not app_api:
            raise KeyError
    except KeyError:
        raise UnknownApp(app_name)
    else:
        try:
            action_api = app_api['actions'][action_name]
            return action_api.get('parameters', [])
        except KeyError:
            raise UnknownAppAction(app_name, action_name)


def get_app_action_default_return(app, action):
    """
    Gets the default return code for a given app and action

    Args:
        app (str): Name of the app
        action (str): Name of the action

    Returns:
        (str): The name of the default return code or Success if none defined
    """
    try:
        app_api = json.loads(redis_cache.hget("app-apis", app))
        if not app_api:
            raise KeyError
    except KeyError:
        raise UnknownApp(app)
    else:
        try:
            action_api = app_api['actions'][action]
            if 'default_return' in action_api:
                return action_api['default_return']
            else:
                return 'Success'
        except KeyError:
            raise UnknownAppAction(app, action)


def get_app_action_return_is_failure(app, action, status):
    """
    Checks the api for whether a status code is a failure code for a given app and action

    Args:
        app (str): Name of the app
        action (str): Name of the action
        status (str): Name of the status

    Returns:
        (boolean): True if status is a failure code, false otherwise
    """
    if status == 'UnhandledException':
        return True
    try:
        app_api = json.loads(redis_cache.hget("app-apis", app))
        if not app_api:
            raise KeyError
    except KeyError:
        raise UnknownApp(app)
    else:
        try:
            action_api = app_api['actions'][action]
            if 'failure' in action_api['returns'][status]:
                return action_api['returns'][status]['failure']
            else:
                return False
        except KeyError:
            raise UnknownAppAction(app, action)


def split_api_params(api, data_param_name):
    """Return a dict with data_param_name entry not included

    Args:
        api (dict): The API
        data_param_name (str): The name of the param to exclude from the dictionary

    Returns:
        dict: The new dictionary with the data_param_name entry removed
    """
    args = []
    for api_param in api:
        if api_param['name'] != data_param_name:
            args.append(api_param)
    return args


# Exceptions
class InvalidAppStructure(Exception):
    pass


class UnknownApp(Exception):
    def __init__(self, app):
        super(UnknownApp, self).__init__('Unknown app {0}'.format(app))
        self.app = app


class UnknownFunction(Exception):
    def __init__(self, app, function_name, function_type):
        self.message = 'Unknown {0} {1} for app {2}'.format(function_type, function_name, app)
        super(UnknownFunction, self).__init__(self.message)
        self.app = app
        self.function = function_name


class UnknownAppAction(UnknownFunction):
    def __init__(self, app, action_name):
        super(UnknownAppAction, self).__init__(app, action_name, 'action')


class UnknownDevice(Exception):
    def __init__(self, app, device_type):
        super(UnknownDevice, self).__init__('Unknown device {0} for device {1} '.format(app, device_type))
        self.app = app
        self.device_type = device_type


class InvalidParameter(Exception):
    def __init__(self, message, errors=None):
        self.message = message
        self.errors = errors or {}
        super(InvalidParameter, self).__init__(self.message)


class UnknownCondition(UnknownFunction):
    def __init__(self, app, condition_name):
        super(UnknownCondition, self).__init__(app, condition_name, 'condition')


class UnknownTransform(UnknownFunction):
    def __init__(self, app, transform_name):
        super(UnknownTransform, self).__init__(app, transform_name, 'transform')


class InvalidApi(Exception):
    pass
