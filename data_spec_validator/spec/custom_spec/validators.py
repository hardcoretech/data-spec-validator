from django.apps import apps

from ..defines import BaseValidator
from .defines import EXIST


def to_param_set(raw_values):
    return {int(x) if x is not None else None for x in raw_values}


# DB (Project) related =========================================================
class ExistValidator(metaclass=BaseValidator):
    name = EXIST

    @staticmethod
    def validate(value, extra, data):
        model_info = extra.get(ExistValidator.name)
        app_str, model_str = model_info.split('.')
        model_cls = apps.get_model(app_str, model_str)
        return model_cls.objects.filter(pk=value).exists(), PermissionError(f'{model_info} has no pk:{value}')
