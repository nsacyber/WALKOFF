import json


def main(args, value):
    """
    Compares the value of of an input using ==, >, <, >=, or <=. See data/functions.json for argument information
    Returns:
        The result of the comparison
    """
    if not args["type"] or args["type"] == "json":
        var = len(json.loads(value))
    else:
        try:
            var = int(value)
        except ValueError:
            var = len(value)

    threshold = args["threshold"]

    if args["operator"] == "g":
        if var > threshold:
            return True

    elif args["operator"] == "ge":
        if var >= threshold:
            return True

    elif args["operator"] == "l":
        if var < threshold:
            return True

    elif args["operator"] == "le":
        if var <= threshold:
            return True

    elif args["operator"] == "e":
        if var == threshold:
            return True
    else:
        if var == threshold:
            return True

    return False
