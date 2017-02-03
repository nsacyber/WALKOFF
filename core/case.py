import uuid, datetime
from functools import partial

import logging

logging.basicConfig()


class Case(object):
    def __init__(self, id="", history=None, subscriptions=None):
        self.id = id
        self.uid = uuid.uuid4()
        self.history = history if history is not None else []
        self.enabled = False
        self.subscriptions = subscriptions if subscriptions is not None else {}

    def __enter__(self):
        self.enabled = True

    def __exit__(self, exception_type, exception_value, traceback):
        self.enabled = False

    def add_event(self, event):
        self.history.append(event)

    def __repr__(self):
        return str({'id': self.id,
                    'history': str(self.history),
                    'subscriptions': str(self.subscriptions)})


cases = {}


def addCase(name, case):
    if name not in cases:
        cases[name] = case
        return True
    return False


def __create_event_entry(sender, entry_message, entry_type, data=None, name=""):
    name = (sender.name if hasattr(sender, "name") else sender.id) if not name else name

    return {
        "uuid": str(uuid.uuid4()),
        "timestamp": str(datetime.datetime.utcnow()),
        "type": entry_type,
        "caller": name,
        "message": entry_message,
        "data": data
    }


def __add_entry_to_case(sender, event, entry_condition):
    for case in cases:
        if cases[case].enabled:
            for key in cases[case].subscriptions:
                if entry_condition(sender, case, key):
                    cases[case].add_event(event=event)


def __add_entry_to_case_wrapper(sender, event_type, entry_condition, message_name, entry_message):
    event_entry = __create_event_entry(sender, event_type, entry_message)
    __add_entry_to_case(sender, event_entry, partial(entry_condition, message_name=message_name))


def __add_entry(message_name, event_type, entry_condition, entry_message):
    return partial(__add_entry_to_case_wrapper,
                   event_type=event_type,
                   entry_condition=entry_condition,
                   message_name=message_name,
                   entry_message=entry_message)


def __is_message_tracked(message_name, case, subscription_key):
    return message_name in cases[case].subscriptions[subscription_key]

# System Cases


def __system_entry_condition(sender, case, subscription_key, message_name):
    return sender.name in cases[case].subscriptions and __is_message_tracked(message_name, case, subscription_key)


def add_system_entry(entry_message):
    return partial(__add_entry,
                   event_type='SYSTEM',
                   entry_condition=__system_entry_condition,
                   entry_message=entry_message)


# Workflow Cases

def __workflow_entry_condition(sender, case, subscription_key, message_name):
    return (sender.parentController in cases[case].subscriptions
            and __is_message_tracked(message_name, case, subscription_key))


def add_workflow_entry(entry_message):
    return partial(__add_entry,
                   event_type='WORKFLOW',
                   entry_condition=__workflow_entry_condition,
                   entry_message=entry_message)


#  Step Cases


def __step_entry_condition(sender, case, subscription_key, message_name):
    steps_tracked = subscription_key.split(':')
    return ((sender.parent_workflow == steps_tracked[0] if steps_tracked else False)
            and __is_message_tracked(message_name, case, subscription_key))


def add_step_entry(entry_message):
    return partial(__add_entry,
                   event_type='STEP',
                   entry_condition=__step_entry_condition,
                   entry_message=entry_message)


#  Next Execution Event Cases
def __is_step_tracked(sender_id, subscription_key):
    steps_tracked = subscription_key.split(':')
    return sender_id in steps_tracked[1:] if len(steps_tracked) > 1 else False


def __next_step_entry_condition(sender, case, subscription_key, message_name):
    return __is_step_tracked(sender.id, subscription_key) and __is_message_tracked(message_name, case, subscription_key)


def add_next_step_entry(entry_message):
    return partial(__add_entry,
                   event_type='NEXT',
                   entry_condition=__next_step_entry_condition,
                   entry_message=entry_message)


#  Flag Events


def __flag_entry_condition(sender, case, subscription_key, message_name):
    return __is_step_tracked(sender.id, subscription_key) and __is_message_tracked(message_name, case, subscription_key)


def add_flag_entry(entry_message):
    return partial(__add_entry,
                   event_type='FLAG',
                   entry_condition=__flag_entry_condition,
                   entry_message=entry_message)

# Filter Events


def __filter_entry_condition(sender, case, subscription_key, message_name):
    return __is_step_tracked(sender.id, subscription_key) and __is_message_tracked(message_name, case, subscription_key)


def add_filter_entry(entry_message):
    return partial(__add_entry,
                   event_type='FILTER',
                   entry_condition=__filter_entry_condition,
                   entry_message=entry_message)