from abc import ABCMeta
from enum import Enum
from functools import lru_cache

# TYPE
NONE = 'none'
INT = 'int'
DIGIT_STR = 'digit_str'  # URL params cannot distinguish from strings and numbers
STR = 'str'
BOOL = 'bool'
JSON = 'json'
JSON_BOOL = 'json_bool'
LIST = 'list'
DICT = 'dict'
SELF = 'self'

# VALUE
DATE = 'date'
DATE_RANGE = 'date_range'
AMOUNT = 'amount'
AMOUNT_RANGE = 'amount_range'
LENGTH = 'length'
DECIMAL_PLACE = 'decimal_place'
OPTIONAL = 'optional'
SPEC = 'spec'
LIST_OF = 'list_of'
ONE_OF = 'one_of'
DUMMY = 'dummy'
ANY_KEY_EXISTS = 'any_key_exists'
KEY_COEXISTS = 'key_coexists'
EMAIL = 'email'
UUID = 'uuid'

# Wrapper prefix
_wrapper_splitter = '-'
_not_prefix = 'not'


def not_(check):
    return _not_prefix + _wrapper_splitter + check


def get_default_check_2_validator_map():
    from spec.validators import (
        AmountRangeValidator,
        AmountValidator,
        AnyKeyExistsValidator,
        BoolValidator,
        DateRangeValidator,
        DateValidator,
        DecimalPlaceValidator,
        DictValidator,
        DigitStrValidator,
        DummyValidator,
        EmailValidator,
        IntValidator,
        JSONBoolValidator,
        JSONValidator,
        KeyCoexistsValidator,
        LengthValidator,
        ListOfValidator,
        ListValidator,
        NoneValidator,
        OneOfValidator,
        OptionalValidator,
        SpecValidator,
        StrValidator,
        UUIDValidator,
    )

    return {
        INT: IntValidator(),
        STR: StrValidator(),
        DIGIT_STR: DigitStrValidator(),
        BOOL: BoolValidator(),
        DICT: DictValidator(),
        LIST: ListValidator(),
        NONE: NoneValidator(),
        JSON: JSONValidator(),
        JSON_BOOL: JSONBoolValidator(),
        ONE_OF: OneOfValidator(),
        OPTIONAL: OptionalValidator(),
        SPEC: SpecValidator(),
        LIST_OF: ListOfValidator(),
        LENGTH: LengthValidator(),
        AMOUNT: AmountValidator(),
        AMOUNT_RANGE: AmountRangeValidator(),
        DECIMAL_PLACE: DecimalPlaceValidator(),
        DATE: DateValidator(),
        DATE_RANGE: DateRangeValidator(),
        DUMMY: DummyValidator(),
        ANY_KEY_EXISTS: AnyKeyExistsValidator(),
        KEY_COEXISTS: KeyCoexistsValidator(),
        EMAIL: EmailValidator(),
        UUID: UUIDValidator(),
    }


@lru_cache(1)
def _get_wrapper_cls_map():
    from .wrappers import NotWrapper

    return {
        NotWrapper.name: NotWrapper,
    }


@lru_cache(1)
def _get_check_2_validator_map():
    from .custom_spec.defines import get_custom_check_2_validator_map

    default_map = get_default_check_2_validator_map()
    custom_map = get_custom_check_2_validator_map()
    validator_map = {**default_map, **custom_map}
    return validator_map


def get_validator(check):
    found_idx = check.find(_wrapper_splitter)
    validator_map = _get_check_2_validator_map()
    ori_validator = validator_map.get(check[found_idx + 1 :], validator_map[DUMMY])
    if found_idx > 0:
        wrapper_cls_map = _get_wrapper_cls_map()
        wrapper_cls = wrapper_cls_map.get(check[:found_idx])
        wrapper = wrapper_cls(ori_validator.validate)
        return wrapper
    else:
        return ori_validator


@lru_cache(1)
def get_unknown_field_value():
    return UnknownFieldValue()


class BaseValidator(ABCMeta):
    @staticmethod
    def validate(value, extra, data):
        raise NotImplementedError


class ValidateResult:
    def __init__(self, spec=None, field=None, check=None, error=None):
        self.spec = type(spec)
        self.field = field
        self.check = check
        self.error = error

    def __str__(self):
        return f'{self.spec}/{self.field}/{self.check}/{self.error}'


class UnknownFieldValue:
    message = 'This field cannot be found in this SPEC'


class CheckerOP(Enum):
    ALL = 'all'
    # All checks will be validated even when the OP is 'any'
    ANY = 'any'


class Checker:
    def __init__(self, checks, op=CheckerOP.ALL, extra=None):
        self.checks = checks
        self.op = op
        self.extra = extra or {}
