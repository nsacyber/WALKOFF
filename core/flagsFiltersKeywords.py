import importlib

def executeFlag(args, value, function):
    #Checks if the flag exists
    try:
        flagModule = importlib.import_module("core.flags." + function)
    except ImportError as e:
        flagModule = None

    if flagModule:
        result = getattr(flagModule, "main")(args=args, value=value)
        return result
    return None


def executeFilter(function, args, value):
    try:
        filterModule = importlib.import_module("core.filters." + function)
    except ImportError as e:
        filterModule = None

    if filterModule:
        result = getattr(filterModule, "main")(args=args, value=value)
        return result
    return value