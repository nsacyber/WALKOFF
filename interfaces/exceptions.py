from six import string_types


class UnknownEvent(Exception):
    """Exception thrown when an unknown or unallowed event(s) is encountered

    Attributes:
        message (str): The error message

    Args:
        events (str|WalkoffEvent|iterable(str|WalkoffEvent)): The unallowed event(s)
    """

    def __init__(self, events):
        self.message = 'Unknown event(s) {}'.format(events if isinstance(events, string_types) else list(events))
        super(Exception, self).__init__(self.message)


class InvalidEventHandler(Exception):
    """Exception thrown when an invalid function is intended to be used as an event handler

    Attributes:
        message (str): The error message

    Args:
        message (str): The error message
    """

    def __init__(self, message):
        self.message = message
        super(Exception, self).__init__(self.message)
