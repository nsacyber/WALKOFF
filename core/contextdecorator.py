def context(fn):
    def wrapper(*args, **kwargs):
        result = fn(*args, **kwargs)
        return result
    return wrapper
