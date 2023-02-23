def is_something_error(error, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except error:
        return True
    return False


def is_type_error(func, *args):
    try:
        func(*args)
    except TypeError:
        return True
    return False
