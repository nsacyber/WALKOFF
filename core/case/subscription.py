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
                if not isinstance(events, list):
                    events = [events]
                return _SubscriptionEventList(events=events)
        else:
            return _SubscriptionEventList()

    def as_json(self):
        return {"events": self.events,
                "all": self.all}

    def __repr__(self):
        return str({'all': self.all, 'events': self.events})


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

    def as_json(self):
        return {"controller": self.controller.as_json(),
                "workflow": self.workflow.as_json(),
                "step": self.step.as_json(),
                "next_step": self.next_step.as_json(),
                "flag": self.flag.as_json(),
                "filter": self.filter.as_json()}

    @staticmethod
    def from_json(json):
        if set(json.keys()) == set(list(['controller', 'workflow', 'step', 'next_step', 'flag', 'filter'])):
             return GlobalSubscriptions(controller=json['controller'],
                                 workflow=json['workflow'],
                                 step=json['step'],
                                 next_step=json['next_step'],
                                 flag=json['flag'],
                                 filter=json['filter'])

    def __repr__(self):
        return str({'controller': self.controller,
                    'workflow': self.workflow,
                    'step': self.step,
                    'next_step': self.next_step,
                    'flag': self.flag,
                    'filter': self.filter})


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
        global_subs_subscribed = global_subs.is_subscribed(message_name) if global_subs is not None else False
        return ((self.events.is_subscribed(message_name) or global_subs_subscribed)
                and not self.disabled.is_subscribed(message_name))

    def as_json(self):
        return {"events": self.events.as_json(),
                "disabled": self.disabled.as_json(),
                "subscriptions": {str(name): subscription.as_json()
                                  for name, subscription in self.subscriptions.items()}}

    def __repr__(self):
        return str({'events': self.events,
                    'disabled': self.disabled,
                    'subscriptions': self.subscriptions})


class CaseSubscriptions(object):
    def __init__(self, subscriptions=None, global_subscriptions=None):
        self.subscriptions = subscriptions if subscriptions is not None else {}
        self.global_subscriptions = global_subscriptions if global_subscriptions is not None else GlobalSubscriptions()

    def is_subscribed(self, ancestry, message_name):
        current_subscriptions = self.subscriptions
        for level, (ancestry_level_name, global_sub) in enumerate(zip(ancestry, self.global_subscriptions)):
            if current_subscriptions and ancestry_level_name in current_subscriptions:
                if (level == len(ancestry) - 1
                    and current_subscriptions[ancestry_level_name].is_subscribed(message_name,
                                                                                 global_subs=global_sub)):
                    return True
                else:
                    current_subscriptions = current_subscriptions[ancestry_level_name].subscriptions
                    continue
            else:
                return False
        else:
            return False

    def as_json(self):
        return {"subscriptions": {str(name): subscription.as_json()
                                  for name, subscription in self.subscriptions.items()},
                "global_subscriptions": self.global_subscriptions.as_json()}

    def __repr__(self):
        return str({'subscriptions': self.subscriptions,
                    'global_subscriptions': self.global_subscriptions})


subscriptions = {}


def set_subscriptions(new_subscriptions):
    global subscriptions
    subscriptions = new_subscriptions
    case_db.register_events(new_subscriptions.keys())


def get_subscriptions():
    return subscriptions

def clear_subscriptions():
    global subscriptions
    subscriptions = {}

def is_case_subscribed(case, ancestry, message_name):
    return subscriptions[case].is_subscribed(ancestry, message_name)


def subscriptions_as_json():
    return {str(name): subscription.as_json() for name, subscription in subscriptions.items()}


def edit_global_subscription(case_name, global_subscriptions):
    if case_name in subscriptions:
        subscriptions[case_name].global_subscriptions = global_subscriptions
        return True
    return False


def edit_subscription(case, ancestry, events):
    if case in subscriptions:
        current_subscriptions = subscriptions[case].subscriptions
        for level, ancestry_level_name in enumerate(ancestry):
            if current_subscriptions and ancestry_level_name in current_subscriptions:
                if level == len(ancestry) - 1:
                    current_subscriptions[ancestry_level_name].events = _SubscriptionEventList(events)
                    return True
                else:
                    current_subscriptions = current_subscriptions[ancestry_level_name].subscriptions
                    continue
            else:
                return False
        else:
            return False
    else:
        return False


def __construct_subscription_from_ancestry(ancestry, events):
    ancestry = list(ancestry[::-1])
    name = ancestry.pop()
    sub = {name: Subscription(events=events)}
    while ancestry:
        name = ancestry.pop()
        sub = {name: Subscription(subscriptions=sub)}
    return sub


def add_subscription(case, ancestry, events):
    if case in subscriptions:
        ancestry = list(ancestry[::-1])
        current_subscriptions = subscriptions[case].subscriptions
        ancestry_level_name = ancestry.pop()
        while ancestry_level_name:
            if not current_subscriptions:
                ancestry.append(ancestry_level_name)
                current_subscriptions = __construct_subscription_from_ancestry(ancestry, events)
                break
            elif ancestry_level_name not in current_subscriptions:
                ancestry.append(ancestry_level_name)
                current_subscriptions[ancestry_level_name] = __construct_subscription_from_ancestry(ancestry, events)[ancestry_level_name]
                break
            else:
                current_subscriptions = current_subscriptions[ancestry_level_name].subscriptions
                ancestry_level_name = ancestry.pop()


def remove_subscription_node(case, ancestry):
    if case in subscriptions:
        ancestry = list(ancestry[::-1])
        current_subscriptions = subscriptions[case].subscriptions
        ancestry_level_name = ancestry.pop()
        while ancestry_level_name and ancestry_level_name in current_subscriptions:
            if not ancestry:
                del current_subscriptions[ancestry_level_name]
                break
            elif not current_subscriptions:
                break
            else:
                current_subscriptions = current_subscriptions[ancestry_level_name].subscriptions
                ancestry_level_name = ancestry.pop()
