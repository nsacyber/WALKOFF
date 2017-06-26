from core.decorators import *


def untagged(value):
    pass


@datafilter
def filter1(value):
    pass


@flag
def flag1(value):
    pass


@datafilter
def filter2(value, arg1):
    return value + arg1

@action
def action1(value):
    pass

@flag
def flag2(value, arg1):
    return (value + arg1) % 2 == 0

def filter3_untagged(value):
    pass


