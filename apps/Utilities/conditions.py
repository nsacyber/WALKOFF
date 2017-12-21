import re

from apps import condition


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
def always_true(value):
    return True


@condition
def always_false(value):
    return False


@condition
def echo_boolean(value):
    return value


@condition
def reverse_boolean(value):
    return not value


@condition
def accept_decline(value):
    return value.lower() == 'accept'

