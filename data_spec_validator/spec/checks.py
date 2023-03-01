import copy
import functools
from enum import Enum
from functools import lru_cache, reduce
from inspect import isclass
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from .defines import (
    AMOUNT,
    AMOUNT_RANGE,
    BOOL,
    COND_EXIST,
    DATE,
    DATE_OBJECT,
    DATE_RANGE,
    DATETIME_OBJECT,
    DECIMAL_PLACE,
    DICT,
    DIGIT_STR,
    DUMMY,
    EMAIL,
    FLOAT,
    FOREACH,
    INT,
    JSON,
    JSON_BOOL,
    LENGTH,
    LIST,
    LIST_OF,
    NONE,
    ONE_OF,
    RAW_CHECK_TYPE,
    REGEX,
    SPEC,
    STR,
    UUID,
    BaseValidator,
    BaseWrapper,
    _wrapper_splitter,
)
from .utils import raise_if

_TYPE = '_type_'


@lru_cache(1)
def _get_default_check_2_validator_map() -> Dict[str, BaseValidator]:
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
        TypeValidator,
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
        _TYPE: TypeValidator(),
    }


def _get_wrapper_cls_map() -> Dict[str, Type[BaseWrapper]]:
    from .wrappers import NotWrapper

    return {
        NotWrapper.name: NotWrapper,
    }


def _get_check_2_validator_map() -> Dict[str, BaseValidator]:
    from .custom_spec.defines import get_custom_check_2_validator_map

    default_map = _get_default_check_2_validator_map()
    custom_map = get_custom_check_2_validator_map()
    validator_map = {**default_map, **custom_map}
    return validator_map


def get_validator(check: str) -> Union[BaseValidator, BaseWrapper]:
    validator_map = _get_check_2_validator_map()

    found_idx = check.find(_wrapper_splitter)
    ori_validator = validator_map.get(check[found_idx + 1 :], validator_map[DUMMY])
    if found_idx > 0:
        wrapper_cls_map = _get_wrapper_cls_map()
        wrapper_cls = wrapper_cls_map.get(check[:found_idx])
        wrapper = wrapper_cls(ori_validator.validate)
        return wrapper
    else:
        return ori_validator


class CheckerOP(Enum):
    ALL = 'all'
    # All checks will be validated even when the OP is 'any'
    ANY = 'any'


class Checker:
    def __init__(
        self,
        raw_checks: List[RAW_CHECK_TYPE],
        optional: bool = False,
        allow_none: bool = False,
        op: CheckerOP = CheckerOP.ALL,
        **kwargs,
    ):
        """
        checks: list of str/class (Check)
        optional: boolean
                  Set optional to True, the validation process will be passed if the field is absent
        allow_none: boolean
                  Set allow_none to True, the field value can be None
        op: CheckerOP
        """
        self.checks, class_check_type = self._sanitize_checks(raw_checks)

        self._op = op
        self._optional = optional
        self._allow_none = allow_none

        self._ensure(kwargs)
        self.extra = self._build_extra(class_check_type, kwargs)

    @staticmethod
    def _sanitize_checks(raw_checks: List[RAW_CHECK_TYPE]) -> Tuple[List[str], Optional[Type[Any]]]:
        class_type_check = None

        def _is_checkable(elem: Any) -> bool:
            return isclass(elem) or type(elem) is str

        def _purify_check(rc: RAW_CHECK_TYPE) -> Union[str, Type[Any]]:
            nonlocal class_type_check
            if isclass(rc):
                raise_if(not _is_checkable(rc), TypeError(f'A qualified CHECK is required, but got {rc}'))
                class_type_check = rc
                return _TYPE
            return rc

        def _convert_class_check(acc: List, raw_check: RAW_CHECK_TYPE) -> List[str]:
            raise_if(not _is_checkable(raw_check), TypeError(f'A qualified CHECK is required, but got {raw_check}'))
            acc.append(_purify_check(raw_check))
            return acc

        ensured = functools.reduce(_convert_class_check, raw_checks, [])
        return ensured, class_type_check

    @staticmethod
    def _build_extra(class_type_check: Optional[Type[Any]], check_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        temp = {_TYPE: class_type_check} if class_type_check else {}
        all_keys = set(_get_check_2_validator_map().keys())

        for arg_k, arg_v in check_kwargs.items():
            lower_arg_k = arg_k.lower()
            if lower_arg_k in all_keys:
                temp.update({lower_arg_k: arg_v})

        extra = copy.deepcopy(temp)
        for arg_k, arg_v in temp.items():
            if arg_k in {LIST_OF, FOREACH}:
                if isclass(arg_v) and _TYPE not in extra:
                    extra.update({arg_k: _TYPE})
                    extra.update({_TYPE: arg_v})
        return extra

    def _ensure(self, check_kwargs: Dict):
        def __ensure_upper_case(_kwargs):
            non_upper = list(filter(lambda k: not k.isupper(), _kwargs.keys()))
            raise_if(bool(non_upper), TypeError(f'Keyword must be upper-cased: {non_upper}'))

        def __ensure_no_repeated_forbidden(_kwargs: Dict):
            blacklist = {'optional', 'allow_none', 'op'}

            def _check_in_blacklist(acc: set, key: str):
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
