def main(args, value):
    try:
        if type(value) == 'int':
            return value
        else:
            result = len(value)
            return result
    except Exception:
        return None