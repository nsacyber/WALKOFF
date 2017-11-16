import logging

from core.case import database

subscriptions = {}

logger = logging.getLogger(__name__)


def set_subscriptions(new_subscriptions):
    """ Resets the subscriptions
    
    Args:
        new_subscriptions (dict({str: {str: [list(str}): The new subscriptions.
            Takes the form of "{case_name: {uid: [events]}"
    """
    global subscriptions
    subscriptions = new_subscriptions
    new_cases = new_subscriptions.keys()
    existing_cases = {x[0] for x in
                      database.case_db.session.query(database.Case).with_entities(database.Case.name).all()}
    database.case_db.delete_cases(existing_cases - set(new_cases))
    database.case_db.add_cases(set(new_cases) - existing_cases)


def add_cases(cases):
    """ Adds the cases to the subscriptions
    
    Args:
        cases (dict({str: {str: [list(str}): The cases to add
            Takes the form of "{case_name: {uid: [events]}"
    """
    global subscriptions
    valid_cases = []
    for case_name, case in cases.items():
        if case_name not in subscriptions:
            subscriptions[case_name] = case
            valid_cases.append(case_name)
    database.case_db.add_cases(valid_cases)


def delete_cases(cases):
    """ Deletes the cases from  the subscriptions
    
    Args:
        cases (list[str]): The names of the cases to remove
    """
    global subscriptions
    valid_cases = []
    for case_name in cases:
        if case_name in subscriptions:
            del subscriptions[case_name]
            valid_cases.append(case_name)
    database.case_db.delete_cases(valid_cases)


def rename_case(old_case_name, new_case_name):
    """ Renames a case
    
    Args:
        old_case_name (str): Old Case name
        new_case_name (str): Case's new name
    """
    global subscriptions
    if old_case_name in subscriptions and new_case_name not in subscriptions:
        subscriptions[new_case_name] = subscriptions.pop(old_case_name)
        database.case_db.rename_case(old_case_name, new_case_name)
        return True
    else:
        return False


def clear_subscriptions():
    """ Clears and resets the subscriptions
    """
    global subscriptions
    subscriptions = {}
    database.case_db.session.query(database.Case).delete(synchronize_session='fetch')
    database.case_db.session.commit()


def get_cases_subscribed(originator, message_name):
    """ Gets all the cases which are subscribed to an event from an execution element

    Args:
        originator (str): The uid of the element from which the event originated
        message_name (str): The name of the message to check
    """
    global subscriptions
    return [case for case, case_subscriptions in subscriptions.items()
            if (originator in case_subscriptions and message_name in case_subscriptions[originator])]


def modify_subscription(case, originator, events):
    """ Edits a subscription by changing the events to which a particular caller is subscribed to
    
    Args:
        case (str): The name of the case to edit
        originator (str): The uid of the element from which the event originated
        events (list[str,int]): The new events to which it is subscribed to
        
    Returns:
        True if successfully edited. False otherwise.
    """
    global subscriptions
    if case in subscriptions:
        subscriptions[case][originator] = events


def remove_subscription_node(case, originator):
    """
    Remove a case's subscription to an ancestry
    
    Args:
        case (str): The case to remove a subscription from
        originator (str): The uid of the element from which the event originated
    """
    global subscriptions
    if case in subscriptions:
        subscriptions[case].pop(originator, False)
