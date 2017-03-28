import re


def main(args, value):
    regex = args["regex"]()

    # Accounts for python wildcard bug
    if regex == "*":
        regex = "(.*)"
    pattern = re.compile(regex)
    match_obj = pattern.search(str(value))
    if match_obj:
        return True
    return False
