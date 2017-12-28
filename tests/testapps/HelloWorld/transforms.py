from apps.decorators import transform


@transform
def top_level_filter(value):
    return value


@transform
def length(value):
    """ Gets the length of the value provided to it.

    Returns:
        If the value is a collection, it calls len() on it.
        If it is an int, it simply returns the value passed in"""
    try:
        if isinstance(value, int):
            return value
        else:
            result = len(value)
            return result
    except TypeError:
        return None


@transform
def json_select(json_in, element):
    return json_in[element]


@transform
def filter2(value, arg1):
    return value + arg1


@transform
def sub1_top_filter(value):
    pass


@transform
def filter1(value, arg1):
    return '{0} {1} {2}'.format(value, arg1['a'], arg1['b'])


@transform
def complex_filter(data_in, arg):
    return data_in + arg['a'] + arg['b'] + sum(arg['c'])


@transform
def filter3(value):
    raise ValueError
