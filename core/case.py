import uuid
import datetime
from functools import partial

import logging

logging.basicConfig()


class _SubscriptionEventList(object):
    def __init__(self, events=None, all=False):
        self.all = all
        self.events = events if (events is not None and not self.all) else []

    def is_subscribed(self, message_name):
        return True if self.all else message_name in self.events

    @staticmethod
    def construct(events):
        if events is not None:
            if events == '*':
                return _SubscriptionEventList(all=True)
            else:
                return _SubscriptionEventList(events=events)
        else:
            return _SubscriptionEventList()

    def __repr__(self):
        return str({'all': str(self.all), 'events': str(self.events)})


class GlobalSubscriptions(object):
    def __init__(self, controller=None, workflow=None, step=None, next_step=None, flag=None, filter=None):
        self.controller = _SubscriptionEventList.construct(controller)
        self.workflow = _SubscriptionEventList.construct(workflow)
        self.step = _SubscriptionEventList.construct(step)
        self.next_step = _SubscriptionEventList.construct(next_step)
        self.flag = _SubscriptionEventList.construct(flag)
        self.filter = _SubscriptionEventList.construct(filter)

    def __iter__(self):
        yield self.controller
        yield self.workflow
        yield self.step
        yield self.next_step
        yield self.flag
        yield self.filter


class Subscription(object):
    def __init__(self, events=None, subscriptions=None, disabled=None):
        self.events = _SubscriptionEventList.construct(events)
        self.subscriptions = subscriptions if subscriptions is not None else {}  # in form of {'name' => Subscription()}
        self.disabled = _SubscriptionEventList.construct(disabled)

    def is_subscribed(self, message_name, global_subs=None):
        global_subs = global_subs if global_subs is not None else []
        return ((self.events.is_subscribed(message_name) or global_subs.is_subscribed(message_name))
                and not self.disabled.is_subscribed(message_name))

    def __repr__(self):
        return str({'events': str(self.events),
                    'disabled': str(self.disabled),
                    'subscriptions': str(self.subscriptions)})


class Case(object):
    def __init__(self, id="", history=None, subscriptions=None, global_subscriptions=None):
        self.id = id
        self.uid = uuid.uuid4()
        self.history = history if history is not None else []
        self.enabled = False
        self.subscriptions = subscriptions if subscriptions is not None else {}
        self.global_subscriptions = global_subscriptions if global_subscriptions is not None else GlobalSubscriptions()

    def __enter__(self):
        self.enabled = True

    def __exit__(self, exception_type, exception_value, traceback):
        self.enabled = False

    def add_event(self, event):
        self.history.append(event)

    def __repr__(self):
        return str({'id': self.id,
                    'history': self.history,
                    'subscriptions': self.subscriptions})


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
        "ancestry": str(sender.ancestry),
        "message": entry_message,
        "data": data
    }


def __add_entry_to_case(sender, event, message_name):
    for case in cases:
        if cases[case].enabled:
            subscriptions = cases[case].subscriptions
            for level, (ancestry_level_name, global_sub) in enumerate(zip(sender.ancestry,
                                                                          cases[case].global_subscriptions)):
                if subscriptions and ancestry_level_name in subscriptions:
                    if (level == len(sender.ancestry) - 1
                            and subscriptions[ancestry_level_name].is_subscribed(message_name, global_subs=global_sub)):
                        cases[case].add_event(event=event)
                    else:
                        subscriptions = subscriptions[ancestry_level_name].subscriptions
                        continue
                else:
                    break


def __add_entry_to_case_wrapper(sender, event_type, message_name, entry_message):
    event_entry = __create_event_entry(sender, event_type, entry_message)
    __add_entry_to_case(sender, event_entry, message_name)


def __add_entry(message_name, event_type, entry_message):
    return partial(__add_entry_to_case_wrapper,
                   event_type=event_type,
                   message_name=message_name,
                   entry_message=entry_message)


def add_system_entry(entry_message):
    return partial(__add_entry,
                   event_type='SYSTEM',
                   entry_message=entry_message)


def add_workflow_entry(entry_message):
    return partial(__add_entry,
                   event_type='WORKFLOW',
                   entry_message=entry_message)


def add_step_entry(entry_message):
    return partial(__add_entry,
                   event_type='STEP',
                   entry_message=entry_message)


def add_next_step_entry(entry_message):
    return partial(__add_entry,
                   event_type='NEXT',
                   entry_message=entry_message)


def add_flag_entry(entry_message):
    return partial(__add_entry,
                   event_type='FLAG',
                   entry_message=entry_message)


def add_filter_entry(entry_message):
    return partial(__add_entry,
                   event_type='FILTER',
                   entry_message=entry_message)
