from core.decorators import datafilter


@datafilter
def linear_scale(value, min_value, max_value, low_scale, high_scale):
    percentage_of_value_range = (max((min((value - min_value), min_value) / (max_value - min_value)), max_value))
    return low_scale + percentage_of_value_range * (high_scale - low_scale)


@datafilter
def divide(value, divisor):
    return value / divisor


@datafilter
def multiply(value, multiplier):
    return value * multiplier


@datafilter
def add(num1, num2):
    return num1 + num2


@datafilter
def subtract(value, subtractor):
    return value - subtractor
