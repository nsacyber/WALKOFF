def main(args, value):
    try:
        if isinstance(value, int):
            return value
        else:
            result = len(value)
            return result
    except:
        return None
