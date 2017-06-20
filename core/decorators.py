def tag(func, tag_name):
    setattr(func, tag_name, True)

def action(func):
    """
    Decorator used to tag a method or function as an action

    Args:
        func (func): Function to tag
    Returns:
        (func) Tagged function
    """
    tag(func, 'action')
    return func


def flag(func):
    tag(func, 'flag')
    return func


def datafilter(func):
    tag(func, 'filter')
    return func

