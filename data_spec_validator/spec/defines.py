import warnings
from abc import ABCMeta, abstractmethod
from enum import Enum
from functools import lru_cache, reduce
from typing import Any, Dict, List, Type, Union

from .utils import raise_if

# TYPE
NONE = 'none'
INT = 'int'
FLOAT = 'float'
DIGIT_STR = 'digit_str'  # URL params cannot distinguish from strings and numbers
STR = 'str'
BOOL = 'bool'
JSON = 'json'
JSON_BOOL = 'json_bool'
LIST = 'list'
DICT = 'dict'
DATE_OBJECT = 'date_obj'
DATETIME_OBJECT = 'datetime_obj'
SELF = 'self'

# VALUE
DATE = 'date'
DATE_RANGE = 'date_range'
AMOUNT = 'amount'
AMOUNT_RANGE = 'amount_range'
LENGTH = 'length'
DECIMAL_PLACE = 'decimal_place'
SPEC = 'spec'
LIST_OF = 'list_of'
ONE_OF = 'one_of'
FOREACH = 'foreach'
DUMMY = 'dummy'
ANY_KEY_EXISTS = 'any_key_exists'
KEY_COEXISTS = 'key_coexists'
EMAIL = 'email'
UUID = 'uuid'
REGEX = 'regex'

COND_EXIST = 'cond_exist'

# Wrapper prefix
_wrapper_splitter = '-'
_not_prefix = 'not'


class BaseWrapper:
    def __init__(self, wrapped_func):
        self.wrapped_func = wrapped_func


class BaseValidator(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def validate(value, extra, data):
        raise NotImplementedError


class UnknownFieldValue:
    message = 'This field cannot be found in this SPEC'


def not_(check) -> str:
    return _not_prefix + _wrapper_splitter + check


def get_default_check_2_validator_map() -> Dict[str, BaseValidator]:
    from data_spec_validator.spec.validators import (
        AmountRangeValidator,
        AmountValidator,
        BoolValidator,
        CondExistValidator,
        DateObjectValidator,
        DateRangeValidator,
        DatetimeObjectValidator,
        DateValidator,
        DecimalPlaceValidator,
        DictValidator,
        DigitStrValidator,
        DummyValidator,
        EmailValidator,
        FloatValidator,
        ForeachValidator,
        IntValidator,
        JSONBoolValidator,
        JSONValidator,
        LengthValidator,
        ListOfValidator,
        ListValidator,
        NoneValidator,
        OneOfValidator,
        RegexValidator,
        SpecValidator,
        StrValidator,
        UUIDValidator,
    )

    return {
        INT: IntValidator(),
        FLOAT: FloatValidator(),
        STR: StrValidator(),
        DIGIT_STR: DigitStrValidator(),
        BOOL: BoolValidator(),
        DICT: DictValidator(),
        LIST: ListValidator(),
        NONE: NoneValidator(),
        JSON: JSONValidator(),
        JSON_BOOL: JSONBoolValidator(),
        DATE_OBJECT: DateObjectValidator(),
        DATETIME_OBJECT: DatetimeObjectValidator(),
        ONE_OF: OneOfValidator(),
        SPEC: SpecValidator(),
        LIST_OF: ListOfValidator(),
        LENGTH: LengthValidator(),
        AMOUNT: AmountValidator(),
        AMOUNT_RANGE: AmountRangeValidator(),
        DECIMAL_PLACE: DecimalPlaceValidator(),
        DATE: DateValidator(),
        DATE_RANGE: DateRangeValidator(),
        DUMMY: DummyValidator(),
        EMAIL: EmailValidator(),
        UUID: UUIDValidator(),
        REGEX: RegexValidator(),
        COND_EXIST: CondExistValidator(),
        FOREACH: ForeachValidator(),
    }


def _get_wrapper_cls_map() -> Dict[str, Type[BaseWrapper]]:
    from .wrappers import NotWrapper

    return {
        NotWrapper.name: NotWrapper,
    }


def _get_check_2_validator_map() -> Dict[str, BaseValidator]:
    from .custom_spec.defines import get_custom_check_2_validator_map

    default_map = get_default_check_2_validator_map()
    custom_map = get_custom_check_2_validator_map()
    validator_map = {**default_map, **custom_map}
    return validator_map


def get_validator(check: str) -> Union[BaseValidator, BaseWrapper]:
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
def get_unknown_field_value() -> UnknownFieldValue:
    return UnknownFieldValue()


class ErrorMode(Enum):
    MSE = 'most_significant'
    ALL = 'all'


class DSVError(Exception):
    def __init__(self, *errors: List[Type[Exception]]):
        self._errors = errors

    def __str__(self, *args, **kwargs):
        return repr(self._errors)


class ValidateResult:
    def __init__(self, spec: Type = None, field: str = None, value: Any = None, check: str = None, error=None):
        # TODO: Output spec & check information when there's a debug message level for development.
        self.__spec = spec.__name__ if spec else None
        self.__field = field
        self.__value = value
        self.__check = check
        self.__error = error

    @property
    def spec(self) -> str:
        return self.__spec

    @property
    def field(self) -> str:
        return self.__field

    @property
    def value(self):
        return self.__value

    @property
    def error(self) -> Exception:
        return self.__error


class CheckerOP(Enum):
    ALL = 'all'
    # All checks will be validated even when the OP is 'any'
    ANY = 'any'


class Checker:
    def __init__(
        self,
        checks: List[str],
        optional: bool = False,
        allow_none: bool = False,
        op: CheckerOP = CheckerOP.ALL,
        extra: Union[Dict, None] = None,
        **kwargs,
    ):
        """
        checks: list of str(Check)
        optional: boolean
                  Set optional to True, the validation process will be passed if the field is absent
        allow_none: boolean
                  Set allow_none to True, the field value can be None
        op: CheckerOP
        extra: None or Dict
        """
        self.checks = checks or []
        self._op = op
        self._optional = optional
        self._allow_none = allow_none

        self._ensure(kwargs)

        check_set = set(checks)
        if extra:
            warnings.warn('[DSV] keyword: extra is gonna be deprecated', DeprecationWarning)
        deprecating_checks = {KEY_COEXISTS, ANY_KEY_EXISTS}
        for deprecating_check in deprecating_checks.intersection(check_set):
            if deprecating_check == KEY_COEXISTS:
                warnings.warn(f'[DSV] Use COND_EXIST instead of {deprecating_check.upper()} ', DeprecationWarning)
            elif deprecating_check == ANY_KEY_EXISTS:
                warnings.warn(
                    f'[DSV] Use @dsv_feature(any_keys_set...) instead of {deprecating_check.upper()}',
                    DeprecationWarning,
                )

        self.extra = self._merge_extra_kwargs(extra or {}, kwargs)

    @staticmethod
    def _merge_extra_kwargs(deprecated_extra: Dict, check_kwargs: Dict) -> Dict:
        extra = deprecated_extra.copy()

        all_keys = set(_get_check_2_validator_map().keys())
        for arg_k, arg_v in check_kwargs.items():
            lower_arg_k = arg_k.lower()
            if lower_arg_k in all_keys:
                extra[lower_arg_k] = arg_v
        return extra

    def _ensure(self, check_kwargs: Dict):
        def __ensure_upper_case(_kwargs):
            non_upper = list(filter(lambda k: not k.isupper(), _kwargs.keys()))
            raise_if(bool(non_upper), TypeError(f'Keyword must be upper-cased: {non_upper}'))

        def __ensure_no_repeated_forbidden(_kwargs: Dict):
            blacklist = {'optional', 'allow_none', 'op', 'extra'}

            def _check_in_blacklist(acc, key):
                if key.lower() in blacklist:
                    acc.add(key)
                return acc

            forbidden = list(reduce(_check_in_blacklist, _kwargs.keys(), set()))
            forbidden.sort()
            raise_if(bool(forbidden), TypeError(f'Forbidden keyword arguments: {", ".join(forbidden)}'))

        raise_if(
            self._optional and len(self.checks) == 0, ValueError('Require at least 1 check when set optional=True')
        )

        __ensure_upper_case(check_kwargs)
        __ensure_no_repeated_forbidden(check_kwargs)

    @property
    def allow_none(self) -> bool:
        return self._allow_none

    @property
    def allow_optional(self) -> bool:
        return self._optional

    @property
    def is_op_any(self) -> bool:
        return self._op == CheckerOP.ANY

    @property
    def is_op_all(self) -> bool:
        return self._op == CheckerOP.ALL


class MsgLv(Enum):
    VAGUE = 'vague'
    DEFAULT = 'default'


# TODO: Can make this a per-spec-check scope feature
__message_level = MsgLv.DEFAULT


def get_msg_level() -> MsgLv:
    return __message_level


def reset_msg_level(vague: bool = False):
    """
    Setting vague=True, all error messages will be replaced to 'field: XXX not well-formatted'.
    Otherwise, the message is as usual showing the reason.
    """
    global __message_level
    if vague:
        __message_level = MsgLv.VAGUE
    else:
        __message_level = MsgLv.DEFAULT
