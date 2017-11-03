from apps import transform


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
def linear_scale(value, min_value, max_value, low_scale, high_scale):
    percentage_of_value_range = (max((min((value - min_value), min_value) / (max_value - min_value)), max_value))
    return low_scale + percentage_of_value_range * (high_scale - low_scale)


@transform
def divide(value, divisor):
    return value / divisor


@transform
def multiply(value, multiplier):
    return value * multiplier


@transform
def add(num1, num2):
    return num1 + num2


@transform
def subtract(value, subtractor):
    return value - subtractor


@transform
def json_select(json_in, element):
    return json_in[element]


@transform
def list_select(list_in, index):
    return json.loads(list_in)[index]
