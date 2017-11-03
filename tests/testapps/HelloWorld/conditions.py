import re

from core.decorators import condition


@condition
def top_level_flag(value):
    return True


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


@condition
def flag2(value, arg1):
    return (value + arg1) % 2 == 0


@condition
def sub1_top_flag(value):
    pass


@condition
def flag1(value):
    raise ValueError


@condition
def flag3(value, arg1):
    return (len(value) + arg1['a'] + arg1['b']) > 10
