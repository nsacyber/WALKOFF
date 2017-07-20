from core.decorators import *


def untagged(value):
    pass


@datafilter
def filter3(value):
    raise ValueError


@flag
def flag1(value):
    raise ValueError


@datafilter
def filter1(value, arg1):
    return '{0} {1} {2}'.format(value, arg1['a'], arg1['b'])

@datafilter
def complex_filter(data_in, arg):
    return data_in + arg['a'] + arg['b'] + sum(arg['c'])

@action
def action1(value):
    pass


@flag
def flag2(value, arg1):
    return (len(value) + arg1['a'] + arg1['b']) > 10

def filter3_untagged(value):
    pass


