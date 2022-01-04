from .defines import BaseValidator
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

class SpecObject:
    pass

class Spec:
    __API_ATTRIBUTES = ["validate"]
    __spec_object = None

    @classmethod
    def __create_specObject(cls):
        spec = SpecObject()
        for attribute in dir(cls):
            if attribute.startswith("__"): continue
            if attribute.startswith("_Spec__"): continue
            if attribute in cls.__API_ATTRIBUTES: continue

            setattr(spec, attribute, getattr(cls, attribute))

        return spec

    @classmethod
    def validate(cls, data, **kwargs):
        if (cls.__spec_object is None):
            cls.__spec_object = cls.__create_specObject()

        return validate_data_spec(data, cls.__spec_object, **kwargs)

