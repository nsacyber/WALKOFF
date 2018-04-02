from six import string_types

from .exceptions import UnknownEvent
from walkoff.events import WalkoffEvent


def convert_events(events):
    """Converts events from signal names to WalkoffEvents

    Args:
        events (str|WalkoffEvent|iterable(str|WalkoffEvent)): The events to convert

    Returns:
        set{WalkoffEvent}: The converted events

    Raises:
        UnknownEvent: If any signal name has no corresponding WalkoffEvent
    """
    converted_events = set()
    for event in convert_to_iterable(events):
        if isinstance(event, WalkoffEvent):
            converted_events.add(event)
        else:
            converted_event = WalkoffEvent.get_event_from_signal_name(event)
            if converted_event is None:
                raise UnknownEvent(event)
            converted_events.add(converted_event)
    return converted_events


def validate_events(events='all', allowed_events=set(WalkoffEvent)):
    """Validates a set of events against allowed events. Converts strings to events if possible.

    Args:
        events (str|WalkoffEvent|iterable(str|WalkoffEvent), optional): The event or events to validate.
            Defaults to all events
        allowed_events (iterable(WalkoffEvent), optional): The allowed events. Defaults to all WalkoffEvents

    Returns:
        set(WalkoffEvent): The converted set of events.

    Raises:
        UnknownEvent: If some events passed in are not in available_events
    """
    if events == 'all':
        return set(allowed_events)
    converted_events = convert_events(events)
    if set(converted_events) - set(allowed_events):
        raise UnknownEvent(set(converted_events) - set(allowed_events))
    return converted_events


def add_docstring(docstring):
    """Decorator to add a docstring dynamically to a function

    Args:
        docstring (str): The string to use as the docstring

    Returns:
        func: The function with the added docstring
    """

    def wrapper(func):
        func.__doc__ = docstring
        return func

    return wrapper


def convert_to_iterable(elements):
    """Converts an element or elements to list if it not already iterable

    Args:
        elements (obj|iterable): The object to convert to an iterable if necessary

    Returns:
        iterable: A list containing only the element passed in if the element was a non-string non-iterable.
            The original iterable otherwise
    """
    try:
        if isinstance(elements, string_types):
            return [elements]
        iter(elements)
        return elements
    except TypeError:
        return [elements]
