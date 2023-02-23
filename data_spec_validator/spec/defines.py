from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Any, List, Type, Union

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
EMAIL = 'email'
UUID = 'uuid'
REGEX = 'regex'

COND_EXIST = 'cond_exist'

_TYPE = '_type'

RAW_CHECK_TYPE = Union[str, Type[Any]]


class BaseValidator(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def validate(value, extra, data):
        raise NotImplementedError


# Wrapper prefix
_wrapper_splitter = '-'
_not_prefix = 'not'


class BaseWrapper:
    def __init__(self, wrapped_func):
        self.wrapped_func = wrapped_func


def not_(check: str) -> str:
    return _not_prefix + _wrapper_splitter + check


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
