import json
import re
import uuid
from decimal import Decimal

import dateutil.parser

from .defines import (
    AMOUNT,
    AMOUNT_RANGE,
    ANY_KEY_EXISTS,
    BOOL,
    DATE,
    DATE_RANGE,
    DECIMAL_PLACE,
    DICT,
    DIGIT_STR,
    DUMMY,
    EMAIL,
    INT,
    JSON,
    JSON_BOOL,
    KEY_COEXISTS,
    LENGTH,
    LIST,
    LIST_OF,
    NONE,
    ONE_OF,
    OPTIONAL,
    REGEX,
    SELF,
    SPEC,
    STR,
    UUID,
    BaseValidator,
    CheckerOP,
    UnknownFieldValue,
    ValidateResult,
    get_unknown_field_value,
    get_validator,
)


def _is_checker_op_all(op):
    return op == CheckerOP.ALL


def _is_checker_op_any(op):
    return op == CheckerOP.ANY


def _extract_fields(checker):
    return list(filter(lambda f: type(f) == str and not (f.startswith('__') and f.endswith('__')), dir(checker)))


def _valid_spec_field(data, field, spec):
    checker = getattr(spec, field)

    op = checker.op
    checks = checker.checks
    extra = checker.extra

    if extra.get(SpecValidator.name) == SELF:
        extra[SpecValidator.name] = spec

    if LIST_OF in checks and hasattr(data, 'getlist'):
        # For QueryDict, all query values are put into list for the same key.
        # It should be client side's (Spec maker) responsibility to indicate that
        # whether the field is a list or not.
        value = data.getlist(field, get_unknown_field_value())
    else:
        value = data.get(field, get_unknown_field_value())

    results = []
    for check in checks:
        validator = get_validator(check)
        try:
            ok, error = validator.validate(value, extra, data)
        except AttributeError as ae:
            if check == LIST_OF:
                # During list_of check, the target should be one kind of spec.
                ok, error = False, TypeError(f'{value} is not a spec of {spec}, detail: {ae}')
            else:
                ok, error = False, RuntimeError(f'{ae}')
        except Exception as e:
            # For any unwell-handled case, go this way for now.
            ok, error = False, RuntimeError(f'{e}')
        results.append((ok, ValidateResult(spec, field, check, error)))

    nok_results = [rs for (ok, rs) in results if not ok]
    if _is_checker_op_any(op) and len(nok_results) == len(checks):
        return False, nok_results
    if _is_checker_op_all(op) and nok_results:
        return False, nok_results
    return True, []


def _valid_spec_fields(data, fields, spec):
    rs = [_valid_spec_field(data, f, spec) for f in fields]
    return rs


class DummyValidator(BaseValidator):
    name = DUMMY

    @staticmethod
    def validate(value, extra, data):
        raise NotImplementedError


class IntValidator(BaseValidator):
    name = INT

    @staticmethod
    def validate(value, extra, data):
        return type(value) is int, TypeError(f'{value} is not a integer')


class StrValidator(BaseValidator):
    name = STR

    @staticmethod
    def validate(value, extra, data):
        return type(value) is str, TypeError(f'{value} is not a string')


class NoneValidator(BaseValidator):
    name = NONE

    @staticmethod
    def validate(value, extra, data):
        return value is None, TypeError(f'{value} is not None')


class BoolValidator(BaseValidator):
    name = BOOL

    @staticmethod
    def validate(value, extra, data):
        return type(value) is bool, TypeError(f'{value} is not a boolean')


class JSONValidator(BaseValidator):
    name = JSON

    @staticmethod
    def validate(value, extra, data):
        try:
            json.loads(value)
            ok = True
        except Exception:
            ok = False
        return ok, TypeError(f'{value} is not a json object')


class JSONBoolValidator(BaseValidator):
    name = JSON_BOOL

    @staticmethod
    def validate(value, extra, data):
        try:
            ok = type(json.loads(value)) is bool
        except Exception:
            ok = False
        return ok, TypeError(f'{value} is not a json boolean')


class ListValidator(BaseValidator):
    name = LIST

    @staticmethod
    def validate(value, extra, data):
        return type(value) is list, TypeError(f'{value} is not a list')


class DictValidator(BaseValidator):
    name = DICT

    @staticmethod
    def validate(value, extra, data):
        return type(value) is dict, TypeError(f'{value} is not a dict')


class AmountValidator(BaseValidator):
    name = AMOUNT

    @staticmethod
    def validate(value, extra, data):
        try:
            float(value)
            return True, ''
        except ValueError:
            return False, ValueError(f'Cannot convert {value} to float')


class AmountRangeValidator(BaseValidator):
    name = AMOUNT_RANGE

    @staticmethod
    def validate(value, extra, data):
        amount_range_info = extra.get(AmountRangeValidator.name)
        assert type(amount_range_info) == dict and ('min' in amount_range_info or 'max' in amount_range_info)

        lower_bound = amount_range_info.get('min', float('-inf'))
        upper_bound = amount_range_info.get('max', float('inf'))

        err_msg = f'Amount: {value} is not within {amount_range_info}'
        return lower_bound <= float(value) <= upper_bound, ValueError(err_msg)


class LengthValidator(BaseValidator):
    name = LENGTH

    @staticmethod
    def validate(value, extra, data):
        length_info = extra.get(LengthValidator.name)
        assert type(length_info) == dict and ('min' in length_info or 'max' in length_info)

        lower_bound, upper_bound = length_info.get('min', 1), length_info.get('max')
        assert lower_bound >= 1, 'Make no sense, min is less than 1 for length validator'

        err_msg = f'Length of {value} is not in between {length_info}'
        if upper_bound:
            return lower_bound <= len(value) <= upper_bound, ValueError(err_msg)
        return lower_bound <= len(value), ValueError(err_msg)


class SpecValidator(BaseValidator):
    name = SPEC

    @staticmethod
    def validate(value, extra, data):
        target_spec = extra.get(SpecValidator.name)

        fields = _extract_fields(target_spec)
        results = _valid_spec_fields(value, fields, target_spec)
        failures = [r for r in results if not r[0]]

        ok = len(failures) == 0
        return ok, failures


class ListOfValidator(BaseValidator):
    name = LIST_OF

    @staticmethod
    def validate(values, extra, data):
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
    def validate(value, extra, data):
        options = extra.get(OneOfValidator.name)
        return value in options, ValueError(f'{value} is not one of {options}')


class OptionalValidator(BaseValidator):
    name = OPTIONAL

    @staticmethod
    def validate(value, extra, data):
        return isinstance(value, UnknownFieldValue), ValueError(f'{value} != UnknownFieldValue')


class DecimalPlaceValidator(BaseValidator):
    name = DECIMAL_PLACE

    @staticmethod
    def validate(value, extra, data):
        dp_info = extra.get(DecimalPlaceValidator.name)
        dv = Decimal(str(value))
        dv_tup = dv.as_tuple()
        dv_dp = -1 * dv_tup.exponent if dv_tup.exponent < 0 else 0
        return dv_dp <= dp_info, ValueError(f'Expect decimal places({dp_info}) for value: {value}, ' f'but got {dv_dp}')


class DateValidator(BaseValidator):
    name = DATE

    @staticmethod
    def validate(value, extra, data):
        try:
            dateutil.parser.parse(value).date()
            return True, ''
        except ValueError:
            return False, ValueError(f'Unexpected date format: {value}')


class DateRangeValidator(BaseValidator):
    name = DATE_RANGE

    @staticmethod
    def validate(value, extra, data):
        range_info = extra.get(DateRangeValidator.name)
        assert type(range_info) == dict and ('min' in range_info or 'max' in range_info)

        min_date_str = range_info.get('min', '1970-01-01')
        max_date_str = range_info.get('max', '2999-12-31')
        assert type(min_date_str) == str and type(max_date_str) == str

        min_date = dateutil.parser.parse(min_date_str).date()
        max_date = dateutil.parser.parse(max_date_str).date()
        value_date = dateutil.parser.parse(value).date()
        return min_date <= value_date <= max_date, ValueError(
            f'{value} is not in range {min_date_str} ~ {max_date_str}'
        )


class DigitStrValidator(BaseValidator):
    name = DIGIT_STR

    @staticmethod
    def validate(value, extra, data):
        return type(value) == str and value.isdigit(), TypeError(f'{value} is not a digit str')


class AnyKeyExistsValidator(BaseValidator):
    name = ANY_KEY_EXISTS

    @staticmethod
    def validate(value, extra, data):
        sibling_keys = extra.get(AnyKeyExistsValidator.name, [])
        return any(key in data for key in sibling_keys), ValueError(f'missing key in {sibling_keys} .')


class KeyCoexistsValidator(BaseValidator):
    name = KEY_COEXISTS

    @staticmethod
    def validate(value, extra, data):
        related_keys = extra.get(KeyCoexistsValidator.name, [])
        related_fields = [data.get(key, get_unknown_field_value()) for key in related_keys]
        return (
            all(not isinstance(related_field, UnknownFieldValue) for related_field in related_fields)
            and not isinstance(value, UnknownFieldValue),
            ValueError(f'missing key in {related_keys} .'),
        )


class EmailValidator(BaseValidator):
    name = EMAIL

    # https://stackoverflow.com/questions/201323/how-to-validate-an-email-address-using-a-regular-expression
    regex = r'(?:[a-z0-9!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&\'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])'

    @staticmethod
    def validate(value, extra, data):
        return type(value) == str and re.fullmatch(EmailValidator.regex, value), ValueError(
            f'{value} is not a valid email address'
        )


class UUIDValidator(BaseValidator):
    name = UUID

    @staticmethod
    def validate(value, extra, data):
        try:
            uuid.UUID(value)
            ok = True
        except Exception:
            ok = False
        return ok, ValueError(f'{value} is not an UUID object')


class RegexValidator(BaseValidator):
    name = REGEX

    @staticmethod
    def validate(value, extra, data):
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
            assert False, 'unsupported match method'

        return type(value) == str and match_func(pattern, value), ValueError(
            f'"{value}" does not match "{error_regex_param}"'
        )
