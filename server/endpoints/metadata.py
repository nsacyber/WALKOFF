import os

from flask import send_file
from flask_jwt_extended import jwt_required

import core.config.config
import core.config.paths
from core import helpers
from core.events import WalkoffEvent, EventType
from server.returncodes import SUCCESS
from server.security import roles_accepted_for_resources, ResourcePermissions


def read_all_possible_subscriptions():
    event_dict = {EventType.playbook.name: []}
    for event in (event for event in WalkoffEvent if event.is_loggable()):
        if event.event_type.name not in event_dict:
            event_dict[event.event_type.name] = [event.signal_name]
        else:
            event_dict[event.event_type.name].append(event.signal_name)
    ret = [{'type': event_type.name, 'events': sorted(event_dict[event_type.name])}
           for event_type in EventType if event_type != EventType.other]

    @jwt_required
    @roles_accepted_for_resources(ResourcePermissions('cases', ['read']))
    def __func():
        return ret, SUCCESS

    return __func()


def read_all_interfaces():
    @jwt_required
    @roles_accepted_for_resources(ResourcePermissions('apps', ['read']))
    def __func():
        return helpers.list_interfaces(), SUCCESS

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
