from core.decorators import *

@datafilter
def top_level_filter(value):
    return value

@flag
def top_level_flag(value):
    return True

@datafilter
def filter1(value):
    pass