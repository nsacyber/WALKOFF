import datetime
import json
from six import string_types

import walkoff.case.subscription as case_subscription
from walkoff.case import database
from walkoff.case.database import Event


def add_entry_to_case(sender, data, event_type, entry_message, message_name):
    """Adds an entry to all appropriate case logs

    Args:
        sender (Object|dict): Object that initiated the event
        data (dict|str): The data for the event
        event_type (str): The type of event
        entry_message (str): The message for the event entry
        message_name (str): The name of the message
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

