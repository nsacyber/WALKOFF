from gevent.event import AsyncResult
from gevent import Timeout
from core.helpers import get_function_arg_names

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
    tag(func, 'action')
    return func


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
        def wrapper(*args):
            result = AsyncResult()

            @event_.connect
            def send(data):
                if len(args) > 1:
                    result.set(func(args[0], data, *args[1:]))
                else:
                    result.set(func(args[0], data))

            try:
                result = result.get(timeout=timeout)
            except Timeout:
                result = 'Getting event {0} timed out at {1} seconds'.format(event_.name, timeout)

            event_.disconnect(send)
            return result

        tag(wrapper, 'action')
        wrapper.__arg_names = get_function_arg_names(func)
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

