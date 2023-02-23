import copy
import datetime
import json
import re
import uuid
from decimal import Decimal
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Tuple, Type, Union

import dateutil.parser

from .checks import (
    _TYPE,
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
    REGEX,
    SPEC,
    STR,
    UUID,
    Checker,
    get_validator,
)
from .defines import SELF, BaseValidator, ValidateResult
from .features import get_any_keys_set, is_strict
from .utils import raise_if

_ALLOW_UNKNOWN = 'ALLOW_UNKNOWN'
_SPEC_WISE_CHECKS = [COND_EXIST]


class UnknownFieldValue:
    message = 'This field cannot be found in this SPEC'


@lru_cache(1)
def get_unknown_field_value() -> UnknownFieldValue:
    return UnknownFieldValue()


def _extract_value(checks: list, data: dict, field: str):
    if LIST_OF in checks and hasattr(data, 'getlist'):
        # For QueryDict, all query values are put into list for the same key.
        # It should be client side's (Spec maker) responsibility to indicate that
        # whether the field is a list or not.
        value = data.getlist(field, get_unknown_field_value())
    else:
        value = data.get(field, get_unknown_field_value())
    return value


def _makeup_internals_to_extra(spec: Type, checks: List[str], raw_extra: Dict, allow_optional: bool) -> Dict:
    extra = copy.deepcopy(raw_extra)
    if extra.get(SpecValidator.name) == SELF:
        extra[SpecValidator.name] = spec

    if COND_EXIST in checks and allow_optional:
        extra[_ALLOW_UNKNOWN] = True
    return extra


def _pass_optional(allow_optional: bool, checks: List[str], value: Any) -> bool:
    return value == get_unknown_field_value() and allow_optional and COND_EXIST not in checks


def _pass_none(allow_none: bool, value: Any) -> bool:
    return value is None and allow_none


def _pass_unknown(_extra: Dict, value: Any) -> bool:
    return value == get_unknown_field_value() and _ALLOW_UNKNOWN in _extra


def _validate_field(data, field, spec) -> Tuple[bool, List[ValidateResult]]:
    checker = getattr(spec, field)

    checks = checker.checks
    allow_optional = checker.allow_optional
    allow_none = checker.allow_none

    value = _extract_value(checks, data, field)
    extra = _makeup_internals_to_extra(spec, checks, checker.extra, allow_optional)

    results = []

    if _pass_optional(allow_optional, checks, value):
        # Skip all the other checks' validations
        return True, []
    elif _pass_none(allow_none, value):
        # Skip all the other checks' validations
        return True, []
    else:

        def _do_validate(_acc_results: List, _spec: Any, _check: str, _value: Any, _data: Dict, _extra: Dict) -> None:
            validator = get_validator(_check)
            try:
                ok, error = validator.validate(_value, _extra, _data)
            except AttributeError as ae:
                if _check == LIST_OF:
                    # During list_of check, the target should be one kind of spec.
                    ok, error = False, TypeError(f'{repr(_value)} is not a spec of {_spec}, detail: {repr(ae)}')
                else:
                    ok, error = False, RuntimeError(f'{repr(ae)}')
            except NotImplementedError:
                raise
            except Exception as e:
                # For any unwell-handled case, go this way for now.
                ok, error = False, RuntimeError(f'{repr(e)}')
            _acc_results.append((ok, ValidateResult(spec, field, _value, _check, error)))

        spec_wise_checks = set(filter(lambda c: c in _SPEC_WISE_CHECKS, checks))
        field_wise_checks = set(checks) - spec_wise_checks

        for chk in spec_wise_checks:
            _do_validate(results, spec, chk, value, data, extra)

        if not _pass_unknown(extra, value):
            for chk in field_wise_checks:
                _do_validate(results, spec, chk, value, data, extra)

    nok_results = [rs for (ok, rs) in results if not ok]
    if checker.is_op_any and len(nok_results) == len(checks):
        return False, nok_results
    if checker.is_op_all and nok_results:
        return False, nok_results
    return True, []


def _validate_spec_features(data, fields, spec) -> Tuple[bool, List[ValidateResult]]:
    if is_strict(spec):
        unexpected = set(data.keys()) - set(fields)
        if unexpected:
            error = ValueError(f'Unexpected field keys({unexpected}) found in strict mode spec')
            return False, [ValidateResult(spec, str(unexpected), data, 'strict', error)]

    any_keys_set = get_any_keys_set(spec)
    if any_keys_set:
        data_keys = set(data.keys())
        for keys in any_keys_set:
            if data_keys.isdisjoint(set(keys)):
                str_keys = ", ".join(keys)
                error = KeyError('At least one of these fields must exist')
                return False, [ValidateResult(spec, str_keys, data, 'any_keys_set', error)]

    return True, [ValidateResult()]


def _validate_spec_fields(data, fields, spec) -> List[Tuple[bool, List[ValidateResult]]]:
    rs = [_validate_field(data, f, spec) for f in fields]
    return rs


class DummyValidator(BaseValidator):
    name = DUMMY

    @staticmethod
    def validate(value, extra, data):
        raise NotImplementedError


class TypeValidator(BaseValidator):
    name = _TYPE

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        check_type = extra.get(TypeValidator.name)
        ok = type(value) is check_type
        info = '' if ok else TypeError(f'{repr(value)} is not in type: {check_type}')
        return ok, info


class IntValidator(BaseValidator):
    name = INT

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        ok = type(value) is int
        info = '' if ok else TypeError(f'{repr(value)} is not an integer')
        return ok, info


class FloatValidator(BaseValidator):
    name = FLOAT

    @staticmethod
    def validate(value, extra, data):
        ok = type(value) is float
        info = '' if ok else TypeError(f'{repr(value)} is not a float')
        return ok, info


class StrValidator(BaseValidator):
    name = STR

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        ok = type(value) is str
        info = '' if ok else TypeError(f'{repr(value)} is not a string')
        return ok, info


class NoneValidator(BaseValidator):
    name = NONE

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        ok = value is None
        info = '' if ok else TypeError(f'{repr(value)} is not None')
        return ok, info


class BoolValidator(BaseValidator):
    name = BOOL

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        ok = type(value) is bool
        info = '' if ok else TypeError(f'{repr(value)} is not a boolean')
        return ok, info


class JSONValidator(BaseValidator):
    name = JSON

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        try:
            json.loads(value)
            return True, ''
        except Exception as e:
            return False, TypeError(f'{repr(value)} is not a json object, {e.__str__()}')


class JSONBoolValidator(BaseValidator):
    name = JSON_BOOL

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        try:
            ok = type(json.loads(value)) is bool
            info = '' if ok else TypeError(f'{repr(value)} is not a json boolean')
            return ok, info
        except Exception as e:
            return False, TypeError(f'{repr(value)} is not a json object, {e.__str__()}')


class ListValidator(BaseValidator):
    name = LIST

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        ok = type(value) is list
        info = '' if ok else TypeError(f'{repr(value)} is not a list')
        return ok, info


class DictValidator(BaseValidator):
    name = DICT

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        ok = type(value) is dict
        info = TypeError(f'{repr(value)} is not a dict')
        return ok, info


class DateObjectValidator(BaseValidator):
    name = DATE_OBJECT

    @staticmethod
    def validate(value, extra, data):
        ok = type(value) is datetime.date
        info = '' if ok else TypeError(f'{repr(value)} is not a date object')
        return ok, info


class DatetimeObjectValidator(BaseValidator):
    name = DATETIME_OBJECT

    @staticmethod
    def validate(value, extra, data):
        ok = type(value) is datetime.datetime
        info = '' if ok else TypeError(f'{repr(value)} is not a datetime object')
        return ok, info


class AmountValidator(BaseValidator):
    name = AMOUNT

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        try:
            float(value)
            return True, ''
        except ValueError:
            return False, ValueError(f'Cannot convert {repr(value)} to float')


class AmountRangeValidator(BaseValidator):
    name = AMOUNT_RANGE

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        amount_range_info = extra.get(AmountRangeValidator.name)
        raise_if(
            type(amount_range_info) != dict or ('min' not in amount_range_info and 'max' not in amount_range_info),
            RuntimeError(f'Invalid checker configuration: {extra}'),
        )

        lower_bound = amount_range_info.get('min', float('-inf'))
        upper_bound = amount_range_info.get('max', float('inf'))

        ok = lower_bound <= float(value) <= upper_bound
        info = '' if ok else ValueError(f'Amount: {repr(value)} must be between {lower_bound} and {upper_bound}')
        return ok, info


class LengthValidator(BaseValidator):
    name = LENGTH

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        length_info = extra.get(LengthValidator.name)
        raise_if(
            type(length_info) != dict or ('min' not in length_info and 'max' not in length_info),
            RuntimeError(f'Invalid checker configuration: {extra}'),
        )

        lower_bound, upper_bound = length_info.get('min', 0), length_info.get('max')
        raise_if(
            lower_bound < 0,
            RuntimeError('Lower boundary cannot less than 0 for length validator'),
        )

        ok = lower_bound <= len(value) <= upper_bound if upper_bound else lower_bound <= len(value)
        info = '' if ok else ValueError(f'Length of {repr(value)} must be between {lower_bound} and {upper_bound}')
        return ok, info


class SpecValidator(BaseValidator):
    name = SPEC

    @staticmethod
    def _extract_fields(spec) -> List[str]:
        raise_if(type(spec) != type, RuntimeError(f'{spec} should be a spec class'))
        return [f_name for f_name, checker in spec.__dict__.items() if isinstance(checker, Checker)]

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, List[Tuple[bool, List[ValidateResult]]]]:
        target_spec = extra.get(SpecValidator.name)

        fields = SpecValidator._extract_fields(target_spec)

        result = _validate_spec_features(value, fields, target_spec)
        if not result[0]:
            return False, [result]

        results = _validate_spec_fields(value, fields, target_spec)
        failures = [r for r in results if not r[0]]

        ok = len(failures) == 0
        return ok, failures


class ListOfValidator(BaseValidator):
    name = LIST_OF

    @staticmethod
    def validate(values, extra, data) -> Tuple[bool, Union[Exception, str]]:
        if type(values) != list:
            return False, TypeError('Must a be in type: list')

        check = extra.get(ListOfValidator.name)
        validator = get_validator(check)
        for value in values:
            ok, error = validator.validate(value, extra, data)
            if not ok:
                # Early return to save lives.
                return False, error
        return True, ''


class OneOfValidator(BaseValidator):
    name = ONE_OF

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        options = extra.get(OneOfValidator.name)
        ok = value in options
        info = '' if ok else ValueError(f'{repr(value)} is not one of {options}')
        return ok, info


class ForeachValidator(BaseValidator):
    name = FOREACH

    @staticmethod
    def validate(values: Iterable, extra: Dict, data: Dict) -> Tuple[bool, Union[Exception, str]]:
        check = extra.get(ForeachValidator.name)
        validator = get_validator(check)
        for value in values:
            ok, error = validator.validate(value, extra, data)
            if not ok:
                # Early return to save lives.
                return False, error
        return True, ''


class DecimalPlaceValidator(BaseValidator):
    name = DECIMAL_PLACE

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        dp_info = extra.get(DecimalPlaceValidator.name)
        dv = Decimal(str(value))
        dv_tup = dv.as_tuple()
        dv_dp = -1 * dv_tup.exponent if dv_tup.exponent < 0 else 0
        ok = dv_dp <= dp_info
        info = '' if ok else ValueError(f'Expect decimal places({dp_info}) for value: {value!r}, ' f'but got {dv_dp}')
        return ok, info


class DateValidator(BaseValidator):
    name = DATE

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        try:
            dateutil.parser.parse(value).date()
            return True, ''
        except ValueError:
            return False, ValueError(f'Unexpected date format: {repr(value)}')


class DateRangeValidator(BaseValidator):
    name = DATE_RANGE

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        range_info = extra.get(DateRangeValidator.name)
        raise_if(
            type(range_info) != dict or ('min' not in range_info and 'max' not in range_info),
            RuntimeError(f'Invalid checker configuration: {extra}'),
        )

        min_date_str = range_info.get('min', '1970-01-01')
        max_date_str = range_info.get('max', '2999-12-31')
        raise_if(
            type(min_date_str) != str or type(max_date_str) != str,
            RuntimeError(f'Invalid checker configuration(must be str): {extra}'),
        )

        min_date = dateutil.parser.parse(min_date_str).date()
        max_date = dateutil.parser.parse(max_date_str).date()
        value_date = dateutil.parser.parse(value).date()
        ok = min_date <= value_date <= max_date
        info = '' if ok else ValueError(f'{repr(value)} is not in range {min_date_str} ~ {max_date_str}')
        return ok, info


class DigitStrValidator(BaseValidator):
    name = DIGIT_STR

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        ok = type(value) == str and value.isdigit()
        info = '' if ok else TypeError(f'{repr(value)} is not a digit str')
        return ok, info


class EmailValidator(BaseValidator):
    name = EMAIL

    # https://html.spec.whatwg.org/multipage/input.html#valid-e-mail-address
    regex = r'[a-zA-Z0-9.!#$%&\'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        ok = type(value) == str and re.fullmatch(EmailValidator.regex, value)
        info = '' if ok else ValueError(f'{repr(value)} is not a valid email address')
        return ok, info


class UUIDValidator(BaseValidator):
    name = UUID

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        try:
            if not isinstance(value, uuid.UUID):
                uuid.UUID(value)
            return True, ''
        except Exception as e:
            return False, ValueError(f'{repr(value)} is not an UUID object: {e.__str__}')


class RegexValidator(BaseValidator):
    name = REGEX

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        regex_param = extra.get(RegexValidator.name, {})
        pattern = regex_param.get('pattern', '')
        match_method = regex_param.get('method', 'search')
        error_regex_param = regex_param.copy()
        error_regex_param['method'] = match_method

        if match_method == 'match':
            match_func = re.match
        elif match_method == 'fullmatch':
            match_func = re.fullmatch
        elif match_method == 'search':
            match_func = re.search
        else:
            raise RuntimeError(f'unsupported match method: {match_method}')

        ok = type(value) == str and match_func and match_func(pattern, value)
        info = '' if ok else ValueError(f'{repr(value)} does not match "{error_regex_param}"')
        return ok, info


class CondExistValidator(BaseValidator):
    name = COND_EXIST

    @staticmethod
    def validate(value, extra, data) -> Tuple[bool, Union[Exception, str]]:
        allow_unknown = extra.get(_ALLOW_UNKNOWN, False)
        params = extra.get(CondExistValidator.name, {})
        must_with_keys = params.get('WITH', [])
        must_without_keys = params.get('WITHOUT', [])

        if isinstance(value, UnknownFieldValue) and not allow_unknown:
            return False, LookupError('must exist')

        ok = True
        msg = ''
        if must_with_keys and not isinstance(value, UnknownFieldValue):
            ok = all([key in data for key in must_with_keys])
            msg = f'{", ".join(must_with_keys)} must exist' if not ok else msg

        if must_without_keys and not isinstance(value, UnknownFieldValue):
            ok = ok and all([key not in data for key in must_without_keys])
            msg = f'{", ".join(must_without_keys)} must not exist' if not ok else msg

        info = '' if ok else KeyError(msg)
        return ok, info
