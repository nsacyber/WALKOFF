import uuid, datetime


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


cases = {}


def addCase(name, case):
    if name not in cases:
        cases[name] = case
        return True
    return False

def __create_event_entry(caller, entry_message, entry_type, data=None):
    name = caller.name if hasattr(caller, "name") else caller.id

    return {
        "uuid": str(uuid.uuid4()),
        "timestamp": str(datetime.datetime.utcnow()),
        "type": entry_type,
        "caller": name,
        "message": entry_message,
        "data": data
    }


def __add_entry_to_case(caller, event, entry_condition):
    for case in cases:
        if cases[case].enabled:
            for key in cases[case].subscriptions:
                if entry_condition(caller, case, key):
                    cases[case].add_event(event=event)


def __next_step_entry_condition(caller, case, subscription_key):
    return True


# System Cases


def __system_entry_condition(caller, case, subscription_key):
    return caller.name in cases[case].subscriptions


def __add_system_entry_to_case(sender, entry_message, **kwargs):
    event_entry = __create_event_entry(sender, entry_message, "SYSTEM")
    __add_entry_to_case(sender, event_entry, __system_entry_condition)


def add_system_entry(entry_message):
    def callback(sender, **kwargs):
        __add_system_entry_to_case(sender, entry_message, **kwargs)

    return callback


# Workflow Cases

def __workflow_entry_condition(caller, case, subscription_key):
    return caller.parentController in cases[case].subscriptions


def __add_workflow_entry_to_case(sender, entry_message, **kwargs):
    event_entry = __create_event_entry(sender, entry_message, "WORKFLOW")
    __add_entry_to_case(sender, event_entry, __workflow_entry_condition)


def add_workflow_entry(entry_message):
    def callback(sender, **kwargs):
        __add_workflow_entry_to_case(sender, entry_message, **kwargs)

    return callback


#  Step Cases


def __step_entry_condition(caller, case, subscription_key):
    return caller.parent in subscription_key.split(':')


def __add_step_entry_to_case(sender, entry_message, **kwargs):
    event_entry = __create_event_entry(sender, entry_message, "STEP")
    __add_entry_to_case(sender, event_entry, __step_entry_condition)


def add_step_entry(entry_message):
    def callback(sender, **kwargs):
        __add_step_entry_to_case(sender, entry_message, **kwargs)

    return callback


#  Next Execution Event Cases

def __next_step_entry_condition(sender, case, subscription_key):
    return sender.id in subscription_key.split(':')

def __add_next_step_entry_to_case(sender, entry_message, **kwargs):
    event_entry = __create_event_entry(sender, entry_message, "NEXT")
    __add_entry_to_case(sender, event_entry, __next_step_entry_condition)


def add_next_step_entry(entry_message):
    def callback(sender, **kwargs):
        __add_next_step_entry_to_case(sender, entry_message, **kwargs)

    return callback
