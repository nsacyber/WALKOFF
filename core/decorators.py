from gevent.event import AsyncResult
from gevent import Timeout
from core.helpers import get_function_arg_names, InvalidApi
from collections import namedtuple
from functools import wraps
import json

ActionResult = namedtuple('ActionResults', ['result', 'status'])


def action_result_as_json(self):
    try:
        json.dumps(self.result)
        return {"result": self.result, "status": self.status}
    except TypeError:
        return {"result": str(self.result), "status": self.status}
ActionResult.as_json = action_result_as_json


def format_result(result):
    if not isinstance(result, tuple):
        return ActionResult(result, 'Success')
    else:
        return ActionResult(*result)


def tag(func, tag_name):
    setattr(func, tag_name, True)


def action(func):
    """
    Decorator used to tag a method or function as an action

    Args:
        func (func): Function to tag
    Returns:
        (func) Tagged function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return format_result(func(*args, **kwargs))

    tag(wrapper, 'action')
    wrapper.__arg_names = get_function_arg_names(func)
    return wrapper


def event(event_, timeout=300):
    """
    Decorator used to tag an action as an event

    Args:
        event_ (apps.Event): The event to wait for before executing the action
        timeout (int, optional): Seconds to wait for the event to occur. Defaults to 300 (5 minutes).
    Returns:
        (func) Tagged function
    """
    def _event(func):
        arg_names = get_function_arg_names(func)
        if len(arg_names) < 2:
            raise InvalidApi('Event action has too few parameters. '
                             'There must be a "self" and a second parameter to receive data from the event.')

        @wraps(func)
        def wrapper(*args, **kwargs):
            result = AsyncResult()

            @event_.connect
            def send(data):
                if len(kwargs) > 0:
                    result.set(func(args[0], data, **kwargs))
                else:
                    result.set(func(args[0], data))

            try:
                result = result.get(timeout=timeout)
            except Timeout:
                result = 'Getting event {0} timed out at {1} seconds'.format(event_.name, timeout), 'EventTimedOut'

            event_.disconnect(send)
            return format_result(result)

        tag(wrapper, 'action')
        wrapper.__arg_names = arg_names
        wrapper.__event_name = event_.name
        return wrapper

    return _event


def flag(func):
    """
    Decorator used to tag a method or function as a flag

    Args:
        func (func): Function to tag
    Returns:
        (func) Tagged function
    """
    tag(func, 'flag')
    return func


def datafilter(func):
    """
    Decorator used to tag a method or function as a filter

    Args:
        func (func): Function to tag
    Returns:
        (func) Tagged function
    """
    tag(func, 'filter')
    return func
