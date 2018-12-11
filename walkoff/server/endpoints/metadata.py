import os

from flask import send_file
from flask_jwt_extended import jwt_required

import walkoff.config
from walkoff import helpers
from walkoff.security import permissions_accepted_for_resources, ResourcePermissions
from walkoff.server.returncodes import SUCCESS


def read_all_interfaces():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('app_apis', ['read']))
    def __func():
        return helpers.list_interfaces(walkoff.config.Config.INTERFACES_PATH), SUCCESS

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
    f = validate_path(walkoff.config.Config.CLIENT_PATH, filename)
    if f is not None:
        return send_file(f), 200
    else:
        return {"error": "invalid path"}, 463
