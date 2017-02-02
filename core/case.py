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


# System Cases


def __system_entry_condition(sender, case, subscription_key, message_name):
    return (sender.name in cases[case].subscriptions
            and message_name in cases[case].subscriptions[subscription_key])


def __add_system_entry_to_case(sender, message_name, entry_message):
    event_entry = __create_event_entry(sender, entry_message, "SYSTEM")
    __add_entry_to_case(sender, event_entry, partial(__system_entry_condition, message_name=message_name))


def __add_system_entry(message_name, entry_message):
    return partial(__add_system_entry_to_case, message_name=message_name, entry_message=entry_message)


def add_system_entry(entry_message):
    return partial(__add_system_entry, entry_message=entry_message)


# Workflow Cases

def __workflow_entry_condition(sender, case, subscription_key, message_name):
    return (sender.parentController in cases[case].subscriptions
            and message_name in cases[case].subscriptions[subscription_key])


def __add_workflow_entry_to_case(sender, message_name, entry_message):
    event_entry = __create_event_entry(sender, entry_message, "WORKFLOW")
    __add_entry_to_case(sender, event_entry, partial(__workflow_entry_condition, message_name=message_name))


def __add_workflow_entry(message_name, entry_message):
    return partial(__add_workflow_entry_to_case, message_name=message_name, entry_message=entry_message)


def add_workflow_entry(entry_message):
    return partial(__add_workflow_entry, entry_message=entry_message)


#  Step Cases


def __step_entry_condition(sender, case, subscription_key, message_name):
    steps_tracked = subscription_key.split(':')
    return ((sender.parent_workflow == steps_tracked[0] if steps_tracked else False))


def __add_step_entry_to_case(sender, message_name, entry_message, **kwargs):
    event_entry = __create_event_entry(sender, entry_message, "STEP")
    __add_entry_to_case(sender, event_entry, partial(__step_entry_condition, message_name=message_name))


def __add_step_entry(message_name, entry_message):
    return partial(__add_step_entry_to_case, message_name=message_name, entry_message=entry_message)


def add_step_entry(entry_message):
    return partial(__add_step_entry, entry_message=entry_message)


#  Next Execution Event Cases

def __next_step_entry_condition(sender, case, subscription_key, message_name):
    steps_tracked = subscription_key.split(':')
    return ((sender.id in steps_tracked[1:] if len(steps_tracked) > 1 else False)
            and message_name in cases[case].subscriptions[subscription_key])


def __add_next_step_entry_to_case(sender, message_name, entry_message):
    event_entry = __create_event_entry(sender, entry_message, "NEXT")
    __add_entry_to_case(sender, event_entry, partial(__next_step_entry_condition, message_name=message_name))


def __add_next_step_entry(message_name, entry_message):
    return partial(__add_next_step_entry_to_case, message_name=message_name, entry_message=entry_message)


def add_next_step_entry(entry_message):
    return partial(__add_next_step_entry, entry_message=entry_message)


#  Flag Events


def __flag_entry_condition(sender, case, subscription_key, message_name):
    steps_tracked = subscription_key.split(':')
    return ((sender.id in steps_tracked[1:] if len(steps_tracked) > 1 else False)
            and message_name in cases[case].subscriptions[subscription_key])


def __add_flag_entry_to_case(sender, message_name, entry_message):
    event_entry = __create_event_entry(sender, entry_message, "FLAG")
    __add_entry_to_case(sender, event_entry, partial(__flag_entry_condition, message_name=message_name))


def __add_flag_entry(message_name, entry_message):
    return partial(__add_flag_entry_to_case, message_name=message_name, entry_message=entry_message)


def add_flag_entry(entry_message):
    return partial(__add_flag_entry, entry_message=entry_message)


# Filter Events


def __filter_entry_condition(sender, case, subscription_key, message_name):
    steps_tracked = subscription_key.split(':')
    return ((sender.id in steps_tracked[1:] if len(steps_tracked) > 1 else False)
            and message_name in cases[case].subscriptions[subscription_key])


def __add_filter_entry_to_case(sender, message_name, entry_message):
    event_entry = __create_event_entry(sender, entry_message, "FILTER")
    __add_entry_to_case(sender, event_entry, partial(__filter_entry_condition, message_name=message_name))


def __add_filter_entry(message_name, entry_message):
    return partial(__add_filter_entry_to_case, message_name=message_name, entry_message=entry_message)


def add_filter_entry(entry_message):
    return partial(__add_filter_entry, entry_message=entry_message)
