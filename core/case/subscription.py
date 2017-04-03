# from core.context import running_context
from core.case import database

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
        self.controller = controller if controller is not None else []
        self.workflow = workflow if workflow is not None else []
        self.step = step if step is not None else []
        self.next_step = next_step if next_step is not None else []
        self.flag = flag if flag is not None else []
        self.filter = filter if filter is not None else []

    def __iter__(self):
        yield self.controller
        yield self.workflow
        yield self.step
        yield self.next_step
        yield self.flag
        yield self.filter

    def as_json(self):
        return {"controller": self.controller,
                "workflow": self.workflow,
                "step": self.step,
                "next_step": self.next_step,
                "flag": self.flag,
                "filter": self.filter}

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
    """

    def __init__(self, events=None, subscriptions=None):
        self.events = events if events is not None else []
        self.subscriptions = subscriptions if subscriptions is not None else {}  # in form of {'name' => Subscription()}

    def is_subscribed(self, message_name):
        """
        Is the given message subscribed to in this level of execution?
        :param message_name: The given message
        :return (bool): Is the message subscribed to?
        """
        return message_name in self.events

    def as_json(self):
        return {"events": self.events,
                "subscriptions": {str(name): subscription.as_json()
                                  for name, subscription in self.subscriptions.items()}}

    def __repr__(self):
        return str({'events': self.events,
                    'subscriptions': self.subscriptions})


class CaseSubscriptions(object):
    def __init__(self, subscriptions=None, global_subscriptions=None):
        self.subscriptions = subscriptions if subscriptions is not None else {}
        self.global_subscriptions = global_subscriptions if global_subscriptions is not None else GlobalSubscriptions()

    def is_subscribed(self, ancestry, message_name):
        current_subscriptions = self.subscriptions
        ancestry = list(ancestry[::-1])
        ancestry_level_name = ancestry.pop()
        while ancestry_level_name and ancestry_level_name in current_subscriptions:
            if not ancestry:
                return current_subscriptions[ancestry_level_name].is_subscribed(message_name)
            else:
                current_subscriptions = current_subscriptions[ancestry_level_name].subscriptions
                ancestry_level_name = ancestry.pop()
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
    database.case_db.register_events(new_subscriptions.keys())


def add_cases(cases):
    valid_cases = []
    for case_name, case in cases.items():
        if case_name not in subscriptions:
            subscriptions[case_name] = case
            valid_cases.append(case_name)
    database.case_db.register_events(valid_cases)


def delete_cases(cases):
    valid_cases = []
    for case_name in cases:
        if case_name in subscriptions:
            del subscriptions[case_name]
            valid_cases.append(case_name)
    database.case_db.delete_cases(valid_cases)


def rename_case(old_case_name, new_case_name):
    if old_case_name in subscriptions:
        subscriptions[new_case_name] = subscriptions.pop(old_case_name)
        database.case_db.rename_case(old_case_name, new_case_name)


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
        ancestry = list(ancestry[::-1])
        ancestry_level_name = ancestry.pop()
        while ancestry_level_name and ancestry_level_name in current_subscriptions:
            if not ancestry:
                current_subscriptions[ancestry_level_name].events = events
                return True
            else:
                current_subscriptions = current_subscriptions[ancestry_level_name].subscriptions
                ancestry_level_name = ancestry.pop()
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
                current_subscriptions[ancestry_level_name] = __construct_subscription_from_ancestry(ancestry, events)[
                    ancestry_level_name]
                break
            else:
                current_subscriptions = current_subscriptions[ancestry_level_name].subscriptions
                ancestry_level_name = ancestry.pop()
        else:
            #You failed to add anything if you get here
            pass


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
