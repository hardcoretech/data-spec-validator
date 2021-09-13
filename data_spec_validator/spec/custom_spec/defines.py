from data_spec_validator.spec.defines import BaseValidator

_custom_map = dict()


def get_custom_check_2_validator_map():
    return _custom_map


def _get_class_name(instance):
    return instance.__class__.__name__


def register(check_2_validator_map):
    for check, validator in check_2_validator_map.items():
        if not issubclass(type(validator), BaseValidator):
            raise TypeError(f'{_get_class_name(validator)} is not a subclass of BaseValidator')

        if check in _custom_map:
            ori_validator = _custom_map[check]
            print(
                f'[WARNING] Check({check}) already exists, gonna overwrite the validator from '
                f'{_get_class_name(ori_validator)} to {_get_class_name(validator)}'
            )
        _custom_map[check] = validator
    return True
