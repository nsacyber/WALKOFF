from core.decorators import *
import re
import json

@transform
def top_level_filter(value):
    return value

@condition
def top_level_flag(value):
    return True

@transform
def filter1(value):
    pass

@condition
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

@condition
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

@transform
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

@transform
def json_select(json_in, element):
    return json_in[element]

