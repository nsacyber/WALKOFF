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
    pass

@action
def action1(value):
    pass

@flag
def flag2(value, arg1):
    pass

def filter3_untagged(value):
    pass


