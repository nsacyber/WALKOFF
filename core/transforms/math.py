from core.decorators import transform


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
