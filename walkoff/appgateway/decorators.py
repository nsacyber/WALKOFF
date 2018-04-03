from functools import wraps

from walkoff.appgateway.actionresult import ActionResult
from walkoff.helpers import get_function_arg_names
from walkoff.appgateway.walkofftag import WalkoffTag


def format_result(result):
    """Converts a result to an ActionResult object

    Args:
        result (str|tuple): The result of the action

    Returns:
        An ActionResult object with the result included in the object

    """
    if not isinstance(result, tuple):
        return ActionResult(result, None)
    else:
        return ActionResult(*result)


def tag(func, tag_name):
    """Sets a tag for a function

    Args:
        func (func): The function to tag
        tag_name (str): The name of the tag
    """
    setattr(func, tag_name, True)


def action(func):
    """Decorator used to tag a method or function as an action

    Args:
        func (func): Function to tag
    Returns:
        (func) Tagged function
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        return format_result(func(*args, **kwargs))

    WalkoffTag.action.tag(wrapper)
    wrapper.__arg_names = get_function_arg_names(func)
    return wrapper


def condition(func):
    """Decorator used to tag a method or function as a condition

    Args:
        func (func): Function to tag
    Returns:
        (func) Tagged function
    """
    WalkoffTag.condition.tag(func)
    return func


def transform(func):
    """Decorator used to tag a method or function as a transform

    Args:
        func (func): Function to tag
    Returns:
        (func) Tagged function
    """
    WalkoffTag.transform.tag(func)
    return func
