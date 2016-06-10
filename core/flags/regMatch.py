import re

def main(args, value):
    regex = args["regex"]
    #Accounts for python wildcard bug
    if regex == "*":
        regex = "(.*)"
    pattern = re.compile(regex)
    matchObj = pattern.search(value)
    if matchObj:
        return True
    return False