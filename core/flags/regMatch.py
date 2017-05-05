import re


def main(args, value):
    """Matches the input using a regular expression matcher. See data/functions.json for argument information
    
    Returns:
        The result of the comparison
    """
    regex = args["regex"]()

    # Accounts for python wildcard bug
    if regex == "*":
        regex = "(.*)"
    pattern = re.compile(regex)
    match_obj = pattern.search(str(value))
    if match_obj:
        return True
    return False
