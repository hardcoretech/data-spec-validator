from .defines import BaseValidator


class BaseWrapper:
    def __init__(self, wrapped_func):
        self.wrapped_func = wrapped_func


class NotWrapper(BaseWrapper, BaseValidator):
    name = 'not'

    def validate(self, value, extra, data):
        ok, error = self.wrapped_func(value, extra, data)
        msg = ''.join(error.args)
        new_error = type(error)(f'not({msg})')
        return not ok, new_error
