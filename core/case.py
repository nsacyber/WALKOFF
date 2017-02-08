import uuid
import datetime
from functools import partial

import logging

logging.basicConfig()


class _SubscriptionEventList(object):
    """
    Wrapper for a list of events to subscribe to. Can specify which ones or all of them

    Attributes:
        all (bool): Are all events subscribed to?
        events (list[str]): Events which are subscribed to.
    """
    def __init__(self, events=None, all=False):
        self.all = all
        self.events = events if (events is not None and not self.all) else []

    def is_subscribed(self, message_name):
        """
        Is a given message subscribed to in this list?
        :param message_name (str): The given message
        :return (bool): Is the message subsribed to?
        """
        return True if self.all else message_name in self.events

    @staticmethod
    def construct(events=None):
        """
        Constructs a _SubscriptionEventList
        :param events: if events is '*' then all are subscribed to. If a list is given then it is subscribed to those messages
        :return (_SubscriptionEventList):
        """
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
    """
    Specifies the events which are subscribed to by all types of a execution level

    Attributes:
        controller (list[str]): Events subscribed to by all controllers
        workflow (list[str]): Events subscribed to by all workflows
        step (list[str]): Events subscribed to by all steps
        next_step (list[str]): Events subscribed to by all next
        flag (list[str]): Events subscribed to by all flags
        filter (list[str]): Events subscribed to by all filters
    """
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
    """
    Encapsulates the events which are subscribed to for one level of execution. Forms a tree.w

    Attributes:
        events (_SubscriptionEventList): A list of events this level is subscribed to
        subscriptions (dict{str: Subscription}): A list of subscriptions to execution events one level lower
        disabled (_SubscriptionEventList): A list of events which should be ignored from the global subscriptions
    """
    def __init__(self, events=None, subscriptions=None, disabled=None):
        self.events = _SubscriptionEventList.construct(events)
        self.subscriptions = subscriptions if subscriptions is not None else {}  # in form of {'name' => Subscription()}
        self.disabled = _SubscriptionEventList.construct(disabled)

    def is_subscribed(self, message_name, global_subs=None):
        """
        Is the given message subscribed to in this level of execution?
        :param message_name: The given message
        :param global_subs: Global subscriptions for this level of execution
        :return (bool): Is the message subscribed to?
        """
        global_subs = global_subs if global_subs is not None else []
        return ((self.events.is_subscribed(message_name) or global_subs.is_subscribed(message_name))
                and not self.disabled.is_subscribed(message_name))

    def __repr__(self):
        return str({'events': str(self.events),
                    'disabled': str(self.disabled),
                    'subscriptions': str(self.subscriptions)})


class Case(object):
    """
    A log of a set of events

    Attributes:
        id (str): Identification
        uid (uuid4): Unique identification
        history (list[EventEntry]): Event log
        enabled (bool):
        subscriptions dict{str: Subscription}: Event types to log for this case.
        global_subscriptions (GlobalSubscriptions): Subscriptions for all events of a given execution level
    """
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
        """
        Appends an event to the log
        :param event (EntryEvent):
        :return:
        """
        self.history.append(event)

    def __repr__(self):
        return str({'id': self.id,
                    'history': self.history,
                    'subscriptions': self.subscriptions})

"""Global log of event cases"""
cases = {}


def addCase(name, case):
    """
    Add a case to cases
    :param name(str): Name of case
    :param case(Case): Case to add
    :return (bool): Was case successfully added?
    """
    if name not in cases:
        cases[name] = case
        return True
    return False


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
    def __init__(self, sender, entry_message, entry_type, data=None, name=""):
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
    __add_entry_to_case(sender, EventEntry(sender, event_type, entry_message), message_name)


def __add_entry(message_name, event_type, entry_message):
    return partial(__add_entry_to_case_wrapper,
                   event_type=event_type,
                   message_name=message_name,
                   entry_message=entry_message)


def add_system_entry(entry_message):
    """
    Callback to use for blinker Signals which log system events
    :param entry_message(str): message to log
    :return: Closure which can be called twice. First on a message name, then on a sender by the blinker signal
    """
    return partial(__add_entry,
                   event_type='SYSTEM',
                   entry_message=entry_message)


def add_workflow_entry(entry_message):
    """
    Callback to use for blinker Signals which log workflow events
    :param entry_message(str): message to log
    :return: Closure which can be called twice. First on a message name, then on a sender by the blinker signal
    """
    return partial(__add_entry,
                   event_type='WORKFLOW',
                   entry_message=entry_message)


def add_step_entry(entry_message):
    """
    Callback to use for blinker Signals which log step events
    :param entry_message(str): message to log
    :return: Closure which can be called twice. First on a message name, then on a sender by the blinker signal
    """
    return partial(__add_entry,
                   event_type='STEP',
                   entry_message=entry_message)


def add_next_step_entry(entry_message):
    """
    Callback to use for blinker Signals which log next step events
    :param entry_message(str): message to log
    :return: Closure which can be called twice. First on a message name, then on a sender by the blinker signal
    """
    return partial(__add_entry,
                   event_type='NEXT',
                   entry_message=entry_message)


def add_flag_entry(entry_message):
    """
    Callback to use for blinker Signals which log flag events
    :param entry_message(str): message to log
    :return: Closure which can be called twice. First on a message name, then on a sender by the blinker signal
    """
    return partial(__add_entry,
                   event_type='FLAG',
                   entry_message=entry_message)


def add_filter_entry(entry_message):
    """
    Callback to use for blinker Signals which log filter events
    :param entry_message(str): message to log
    :return: Closure which can be called twice. First on a message name, then on a sender by the blinker signal
    """
    return partial(__add_entry,
                   event_type='FILTER',
                   entry_message=entry_message)
