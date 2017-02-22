from core.case.database import case_db


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
        :return (bool): Is the message subscribed to?
        """
        return True if self.all else message_name in self.events

    @staticmethod
    def construct(events=None):
        """
        Constructs a _SubscriptionEventList
        Args:
            events: if events is '*' then all are subscribed to. If a list is given then it is subscribed to those messages
        Returns:
            _SubscriptionEventList:
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


class CaseSubscriptions(object):
    def __init__(self, subscriptions=None, global_subscriptions=None):
        self.subscriptions = subscriptions if subscriptions is not None else {}
        self.global_subscriptions = global_subscriptions if global_subscriptions is not None else GlobalSubscriptions()

    def __repr__(self):
        return str({'subscriptions': str(self.subscriptions),
                    'global_subscriptions': self.global_subscriptions})


subscriptions = {}


def set_subscriptions(new_subscriptions):
    global subscriptions
    subscriptions = new_subscriptions
    case_db.register_events(new_subscriptions.keys())