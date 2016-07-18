def main(args, value):
    try:
        if args["str"]:
            if isinstance(value, str) or isinstance(value, unicode):
                result = str(args["str"]) % value
            else:
                result = args["str"] % tuple(value)
        return result
    except Exception as e:
        print e
        return None