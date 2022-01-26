from .defines import BaseValidator, Checker
from .actions import validate_data_spec

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


class SpecMeta(type):
    def __new__(cls, name, bases, classdict):
        fields = {}
        for key, value in classdict.items():
            if isinstance(value, Checker):
                fields[key] = value

        classdict['_spec_fields'] = fields
        return type.__new__(cls, name, bases, classdict)

    @property
    def spec_fields(cls):
        return cls._spec_fields


class Spec(metaclass = SpecMeta):
    @classmethod
    def validate(cls, data, **kwargs):
        return validate_data_spec(data, cls, **kwargs)
