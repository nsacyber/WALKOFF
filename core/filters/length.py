def main(args, value):
    try:
        result = len(value)
        return result
    except Exception as e:
        print e
        return None