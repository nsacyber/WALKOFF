from core.case import database
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED


class GlobalSubscriptions(object):
    """
    Specifies the events which are subscribed to by all types of a execution level

    Args:
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
        """Gets the JSON representation of all the GlobalSubscription object.
        
        Returns:
            The JSON representation of the GlobalSubscription object.
        """
        return {"controller": self.controller,
                "workflow": self.workflow,
                "step": self.step,
                "next_step": self.next_step,
                "flag": self.flag,
                "filter": self.filter}

    @staticmethod
    def from_json(json_in):
        """Forms a GlobalSubscription object from the provided JSON object.
        
        Args:
            json_in (JSON object): The JSON object to convert from.
            
        Returns:
            The GlobalSubscription object parsed from the JSON object.
        """
        if set(json_in.keys()) == set(list(['controller', 'workflow', 'step', 'next_step', 'flag', 'filter'])):
            return GlobalSubscriptions(controller=json_in['controller'],
                                       workflow=json_in['workflow'],
                                       step=json_in['step'],
                                       next_step=json_in['next_step'],
                                       flag=json_in['flag'],
                                       filter=json_in['filter'])

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

    Args:
        events (_SubscriptionEventList): A list of events this level is subscribed to
        subscriptions (dict{str: Subscription}): A list of subscriptions to execution events one level lower
    """

    def __init__(self, events=None, subscriptions=None):
        """Constructs a subscription object
        
        Args:
            events (list, optional): A list of events ID's to subscribe to. Usually strings or ints. Some can be found
                in core.case.callbacks. Defaults to an empty list
            subscriptions (dict{str: Subscription}, optional): The child nodes of the subscription object.
                Takes the form of "subscription name => Subscription". Defaults to an empty dictionary
        """
        self.events = events if events is not None else []
        self.subscriptions = subscriptions if subscriptions is not None else {}  # in form of {'name' => Subscription()}

    def is_subscribed(self, message_name):
        """Is the given message subscribed to in this level of execution?
        
        Args:
             message_name (str): The given message
             
        Returns:
             Is the message subscribed to?
        """
        return message_name in self.events

    def as_json(self, names=False):
        """Gets the JSON representation of all the subscription object.
        
        Args:
            names (bool, optional): Should the names of the controller events be converted to names? Defaults to False
            
        Returns:
            The JSON representation of the subscription object.
        """
        if names:
            results = {"events": convert_to_event_names(self.events),
                       "subscriptions": {str(name): subscription.as_json()
                                         for name, subscription in self.subscriptions.items()}}
        else:
            results = {"events": self.events,
                       "subscriptions": {str(name): subscription.as_json()
                                         for name, subscription in self.subscriptions.items()}}
        return results

    @staticmethod
    def from_json(json_in):
        """Forms a Subscription object from the provided JSON object.
        
        Args:
            json_in (JSON object): The JSON object to convert from.
            
        Returns:
            The Subscription object parsed from the JSON object.
        """
        events = json_in['events'] if 'events' in json_in else None
        _subscriptions = json_in['subscriptions'] if 'subscriptions' in json_in else None
        if _subscriptions is not None:
            _subscriptions = {sub_name: Subscription.from_json(sub) for sub_name, sub in _subscriptions.items()}
        return Subscription(events=events, subscriptions=_subscriptions)

    def __repr__(self):
        return str({'events': self.events,
                    'subscriptions': self.subscriptions})


class CaseSubscriptions(object):
    """
    An object encapsulating a case's subscriptions and its GlobalSubscriptions
    """

    def __init__(self, subscriptions=None, global_subscriptions=None):
        """ Constructs a case
        
        Args:
            subscriptions (dict{str: Subscription}, optional): The case's subscriptions. Keys should represent the
                controller names. Defaults to an empty dictionary
            global_subscriptions (GlobalSubscriptions, optional): The case's global subscriptions. Defaults to None
        """
        self.subscriptions = subscriptions if subscriptions is not None else {}
        self.global_subscriptions = global_subscriptions if global_subscriptions is not None else GlobalSubscriptions()

    def is_subscribed(self, ancestry, message_name):
        """ Checks if the case is subscribed to an event with the a given message and ancestry
        
        Args:
            ancestry (list[str]): The ancestry of teh sender of the event
            message_name (str, int): The event type
            
        Returns:
             A boolean describing if the case is subscribed to the event or not
        """
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
        """Gets the JSON representation of all the CaseSubscription object.
        
        Returns:
            The JSON representation of the CaseSubscription object.
        """
        return {"subscriptions": {str(name): subscription.as_json()
                                  for name, subscription in self.subscriptions.items()},
                "global_subscriptions": self.global_subscriptions.as_json()}

    @staticmethod
    def from_json(json_in):
        """Forms a CaseSubscription object from the provided JSON object.
        
        Args:
            json_in (JSON object): The JSON object to convert from.
            
        Returns:
            The CaseSubscription object parsed from the JSON object.
        """
        _subscriptions = json_in['subscriptions'] if 'subscriptions' in json_in else None
        if _subscriptions is not None:
            _subscriptions = {subscription_name: Subscription.from_json(subscription)
                              for subscription_name, subscription in _subscriptions.items()}

        global_subscriptions = json_in['global_subscriptions'] if 'global_subscriptions' in json_in else None
        if global_subscriptions is not None:
            global_subscriptions = GlobalSubscriptions.from_json(global_subscriptions)
        return CaseSubscriptions(subscriptions=_subscriptions, global_subscriptions=global_subscriptions)

    def __repr__(self):
        return str({'subscriptions': self.subscriptions,
                    'global_subscriptions': self.global_subscriptions})


subscriptions = {}


def set_subscriptions(new_subscriptions):
    """ Resets the subscriptions
    
    Args:
        new_subscriptions (dict({str: CaseSubscriptions}): The new subscriptions.
            Takes the form of "{subscription_name: CaseSubscriptions}"
    """
    global subscriptions
    subscriptions = new_subscriptions
    database.case_db.add_cases(new_subscriptions.keys())


def add_cases(cases):
    """ Adds the cases to the subscriptions
    
    Args:
        cases dict({str: CaseSubscription}): the cases and their associated subscriptions to add.
            Takes the form of "{subscription_name: CaseSubscriptions}"
    """
    valid_cases = []
    for case_name, case in cases.items():
        if case_name not in subscriptions:
            subscriptions[case_name] = case
            valid_cases.append(case_name)
    database.case_db.add_cases(valid_cases)


def delete_cases(cases):
    """ Deletes the cases from  the subscriptions
    
    Args:
        cases (list[str]): The names of teh cases to remove
    """
    valid_cases = []
    for case_name in cases:
        if case_name in subscriptions:
            del subscriptions[case_name]
            valid_cases.append(case_name)
    database.case_db.delete_cases(valid_cases)


def rename_case(old_case_name, new_case_name):
    """ Renames a case
    
    Args:
        old_case_name (str): Case name to change
        new_case_name (str): Case's new name
    """
    if old_case_name in subscriptions:
        subscriptions[new_case_name] = subscriptions.pop(old_case_name)
        database.case_db.rename_case(old_case_name, new_case_name)


def get_subscriptions():
    """ Gets the subscriptions
    """
    return subscriptions


def clear_subscriptions():
    """ Clears and resets the subscriptions
    """
    global subscriptions
    subscriptions = {}


def is_case_subscribed(case, ancestry, message_name):
    """ Checks if a case is subscribed to a message given a message and its sender's ancestry
    
    Args:
        case (str): The name of the case
        ancestry (list[str]): The ancestry of the sender
        message_name (str): The name of the message to check
    """
    return subscriptions[case].is_subscribed(ancestry, message_name)


def subscriptions_as_json():
    """ Gets a JSON representation of all the cases and case subscriptions
    """
    return {str(name): subscription.as_json() for name, subscription in subscriptions.items()}


def edit_global_subscription(case_name, global_subscriptions):
    """ Edits a case's GlobalSubscription
    
    Args:
        case_name (str): The name of the case to edit
        global_subscriptions (GlobalSubscriptions): The case's new global subscriptions
        
    Returns:
        True if successfully edited. False otherwise.
    """
    if case_name in subscriptions:
        subscriptions[case_name].global_subscriptions = global_subscriptions
        return True
    return False


def edit_subscription(case, ancestry, events):
    """ Edits a subscription by changing the events to which a particular ancestry is subscribed to
    
    Args:
        case (str): The name of the case to edit
        ancestry (list[str]): The ancestry to edit
        events (list[str,int]): The ancestry's new events to which it is subscribed to
        
    Returns:
        True if successfully edited. False otherwise.
    """
    if case in subscriptions:
        a = list(ancestry[::-1])
        current_subscriptions = subscriptions[case].subscriptions
        ancestry = list(ancestry[::-1])
        if ancestry:
            ancestry_level_name = ancestry.pop()
            if ancestry_level_name not in current_subscriptions:
                subscriptions[case].subscriptions = __construct_subscription_from_ancestry(a, events)
                return True
            else:
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
    """
    Adds a subscription of a set events and ancestry to a case
    
    Args:
        case (str): The case to add a subscription to
        ancestry (list[str]): The ancestry to add events to
        events (list[str,int]): The events to subscribe to
    """
    if case in subscriptions:
        ancestry = list(ancestry[::-1])
        current_subscriptions = subscriptions[case].subscriptions
        if ancestry:
            ancestry_level_name = ancestry.pop()
            while ancestry_level_name:
                if not current_subscriptions:
                    ancestry.append(ancestry_level_name)
                    current_subscriptions = __construct_subscription_from_ancestry(ancestry, events)
                    break
                elif ancestry_level_name not in current_subscriptions:
                    ancestry.append(ancestry_level_name)
                    current_subscriptions[ancestry_level_name] = \
                        __construct_subscription_from_ancestry(ancestry, events)[ancestry_level_name]
                    break
                else:
                    current_subscriptions = current_subscriptions[ancestry_level_name].subscriptions
                    ancestry_level_name = ancestry.pop()
            else:
                # You failed to add anything if you get here
                pass


def remove_subscription_node(case, ancestry):
    """
    Remove a case's subscription to an ancestry
    
    Args:
        case (str): The case to remove a subscription from
        ancestry (list[str]): The ancestry to remove from the case's subscriptions
    """
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


__scheduler_event_conversion = {'Scheduler Start': EVENT_SCHEDULER_START,
                                'Scheduler Shutdown': EVENT_SCHEDULER_SHUTDOWN,
                                'Scheduler Paused': EVENT_SCHEDULER_PAUSED,
                                'Scheduler Resumed': EVENT_SCHEDULER_RESUMED,
                                'Job Added': EVENT_JOB_ADDED,
                                'Job Removed': EVENT_JOB_REMOVED,
                                'Job Executed': EVENT_JOB_EXECUTED,
                                'Job Error': EVENT_JOB_ERROR}


def convert_to_event_names(events):
    """
    Converts events to controller event names if event is a controller event
    
    Args:
        events (list[str, int]): Events to be converted
        
    Returns:
        List of event identifiers in which the controller events have been converted to their string representations
    """
    result = []
    for event in events:
        try:
            code = int(event)
            for key in __scheduler_event_conversion:
                if __scheduler_event_conversion[key] == code:
                    result.append(key)
        except:
            result.append(event)
    return result
