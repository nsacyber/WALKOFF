def main(args, value):
    """ Gets the length of the value provided to it.
    
    Returns:
        If the value is a collection, it calls len() on it. If it is an int, it simply returns the value passed in"""
    try:
        if isinstance(value, int):
            return value
        else:
            result = len(value)
            return result
    except:
        return None
