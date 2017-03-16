import datetime
import logging
import uuid
from functools import partial

import core.case.subscription as case_subscription
from core.case.database import case_db

logging.basicConfig()  # needed so apscheduler can log to console when an error occurs


class EventEntry(object):
    """
    Container for event entries

    Attributes:
        uuid (str): a unique identifier
        timestamp (str): time of creation
        type (str): type of event logged
        caller (str): name/id of the object which created the event
        ancestry (list[str]): callchain which produced the event
        message (str): Event message
        data: other information attached to event
    """

    def __init__(self, sender, entry_type, entry_message, data=None, name=""):
        self.uuid = str(uuid.uuid4())
        self.timestamp = str(datetime.datetime.utcnow())
        self.type = entry_type
        self.caller = (sender.name if hasattr(sender, "name") else sender.id) if not name else name
        self.ancestry = list(sender.ancestry)
        self.message = entry_message
        self.data = data

    def __repr__(self):
        return str({
            "uuid": self.uuid,
            "timestamp": self.timestamp,
            "type": str(self.type),
            "caller": str(self.caller),
            "ancestry": str(self.ancestry),
            "message": str(self.message),
            "data": str(self.data)
        })


def __add_entry_to_case_db(sender, event, message_name):
    #print('__add_entry_to_case_db event {0}'.format(event))
    cases_to_add = [case for case in case_subscription.subscriptions
                    if case_subscription.is_case_subscribed(case, sender.ancestry, message_name)]
    case_db.add_event(event, cases_to_add)


def __add_entry_to_case_wrapper(sender, event_type, message_name, entry_message, data):
    __add_entry_to_case_db(sender, EventEntry(sender, event_type, entry_message, data), message_name)


def __add_entry(message_name, event_type, entry_message, data):
    return partial(__add_entry_to_case_wrapper,
                   event_type=event_type,
                   message_name=message_name,
                   entry_message=entry_message,
                   data=data)


def add_system_entry(entry_message, data=''):
    """
    Callback to use for blinker Signals which log system events
    :param entry_message(str): message to log
    :return: Closure which can be called twice. First on a message name, then on a sender by the blinker signal
    """
    return partial(__add_entry,
                   event_type='SYSTEM',
                   entry_message=entry_message,
                   data=data)


def add_workflow_entry(entry_message, data=''):
    """
    Callback to use for blinker Signals which log workflow events
    :param entry_message(str): message to log
    :return: Closure which can be called twice. First on a message name, then on a sender by the blinker signal
    """
    return partial(__add_entry,
                   event_type='WORKFLOW',
                   entry_message=entry_message,
                   data=data)


def add_step_entry(entry_message, data=''):
    """
    Callback to use for blinker Signals which log step events
    :param entry_message(str): message to log
    :return: Closure which can be called twice. First on a message name, then on a sender by the blinker signal
    """
    return partial(__add_entry,
                   event_type='STEP',
                   entry_message=entry_message,
                   data='')


def add_next_step_entry(entry_message, data=''):
    """
    Callback to use for blinker Signals which log next step events
    :param entry_message(str): message to log
    :return: Closure which can be called twice. First on a message name, then on a sender by the blinker signal
    """
    return partial(__add_entry,
                   event_type='NEXT',
                   entry_message=entry_message,
                   data=data)


def add_flag_entry(entry_message, data=''):
    """
    Callback to use for blinker Signals which log flag events
    :param entry_message(str): message to log
    :return: Closure which can be called twice. First on a message name, then on a sender by the blinker signal
    """
    return partial(__add_entry,
                   event_type='FLAG',
                   entry_message=entry_message,
                   data=data)


def add_filter_entry(entry_message, data=''):
    """
    Callback to use for blinker Signals which log filter events
    :param entry_message(str): message to log
    :return: Closure which can be called twice. First on a message name, then on a sender by the blinker signal
    """
    return partial(__add_entry,
                   event_type='FILTER',
                   entry_message=entry_message,
                   data=data)
