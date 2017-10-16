import re
from core.decorators import condition


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
