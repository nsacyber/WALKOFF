import json

def main(args, value):
    if not args["type"] or args["type"] == "json":
        var = len(json.loads(value))
    elif args["type"] == "int":
        var = int(value)
    else:
        var = len(value)

    threshold = int(args["threshold"])

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