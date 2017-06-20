from core.decorators import *
import re


@datafilter
def top_level_filter(value):
    return value

@flag
def top_level_flag(value):
    return True

@datafilter
def filter1(value):
    pass

@flag
def count(value, operator, threshold):
    if operator == 'g' and value > threshold:
        return True

    elif operator == 'ge' and value >= threshold:
        return True

    elif operator == 'l' and value < threshold:
        return True

    elif operator == 'le' and value <= threshold:
        return True

    elif operator == 'e' and value == threshold:
        return True
    else:
        return value == threshold

@flag
def regMatch(value, regex):
    """Matches the input using a regular expression matcher. See data/functions.json for argument information

    Returns:
        The result of the comparison
    """
    if regex == "*":  # Accounts for python wildcard bug
        regex = "(.*)"
    pattern = re.compile(regex)
    match_obj = pattern.search(value)
    return bool(match_obj)

@datafilter
def length(value):
    """ Gets the length of the value provided to it.

    Returns:
        If the value is a collection, it calls len() on it.
        If it is an int, it simply returns the value passed in"""
    try:
        if isinstance(value, int):
            return value
        else:
            result = len(value)
            return result
    except TypeError:
        return None

@datafilter
def json_select(json, path):
    working = json
    for path_element in path:
        working = working[path_element]
    print('Selected: {0}'.format(working))
    return working