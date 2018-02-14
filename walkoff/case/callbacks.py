import datetime
import json
from functools import partial

from blinker import Signal
from six import string_types

import walkoff.case.subscription as case_subscription
from walkoff.case import database
from walkoff.case.database import Event


def add_entry_to_case(sender, data, event_type, entry_message, message_name):
    """Adds an entry to all appropriate case logs
    """
    if isinstance(sender, dict):
        originator = sender['id']
    else:
        originator = sender.id
    cases_to_add = case_subscription.get_cases_subscribed(originator, message_name)
    if cases_to_add:
        if not isinstance(data, string_types):
            try:
                if 'data' in data:
                    data = data['data']
                data = json.dumps(data)
            except TypeError:
                data = str(data)
        event = Event(type=event_type,
                      timestamp=datetime.datetime.utcnow(),
                      originator=originator,
                      message=entry_message,
                      data=data)
        database.case_db.add_event(event, cases_to_add)


def __construct_logging_signal(event_type, message_name, entry_message):
    """Constructs a blinker Signal to log an event to the log database.

    Note:
        The returned callback must be stored to a module variable for the signal to work.
        
    Args:
        event_type (str): Type of event which is logged 'Workflow, Action, etc.'
        message_name (str): Name of message
        entry_message (str): More detailed message to log
        
    Returns:
        (signal, callback): The constructed blinker signal and its associated callback.
    """
    signal = Signal(message_name)
    signal_callback = partial(add_entry_to_case,
                              data='',
                              event_type=event_type,
                              entry_message=entry_message,
                              message_name=message_name)
    signal.connect(signal_callback)
    return signal, signal_callback  # need to return a tuple and save it to avoid weak reference
