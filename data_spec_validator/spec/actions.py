from typing import List, Tuple

from .defines import DSVError, ErrorMode, MsgLv, ValidateResult, get_msg_level
from .features import get_err_mode, repack_multirow
from .utils import raise_if
from .validators import SpecValidator, UnknownFieldValue


def _wrap_error_with_field_info(failure) -> Exception:
    if get_msg_level() == MsgLv.VAGUE:
        return RuntimeError(f'field: {failure.field} not well-formatted')
    if isinstance(failure.value, UnknownFieldValue):
        return LookupError(f'field: {failure.field} missing')
    msg = f'field: {failure.spec}.{failure.field}, reason: {failure.error}'
    return type(failure.error)(msg)


def _flatten_results(failures, errors=None):
    raise_if(type(errors) != list, RuntimeError(f'{errors} not a list'))

    if type(failures) == tuple:
        _flatten_results(failures[1], errors)
    elif type(failures) == list:
        for item in failures:
            _flatten_results(item, errors)
    elif isinstance(failures, ValidateResult):
        if issubclass(type(failures.error), Exception):
            error = _wrap_error_with_field_info(failures)
            errors.append(error)
            return
        _flatten_results(failures.error, errors)


def _find_most_significant_error(errors: List[Exception]) -> Exception:
    # Build error list by error types
    err_map = {}
    for err in errors:
        if isinstance(err, ValueError):
            err_key = 'ValueError'
        elif isinstance(err, PermissionError):
            err_key = 'PermissionError'
        elif isinstance(err, TypeError):
            err_key = 'TypeError'
        elif isinstance(err, LookupError):
            err_key = 'LookupError'
        elif isinstance(err, KeyError):
            err_key = 'KeyError'
        else:
            err_key = 'RuntimeError'
        err_map.setdefault(err_key, []).append(err)

    # Severity, PermissionError > LookupError > TypeError > ValueError > RuntimeError.
    errors = (
        err_map.get('PermissionError', [])
        or err_map.get('KeyError', [])
        or err_map.get('LookupError', [])
        or err_map.get('TypeError', [])
        or err_map.get('ValueError', [])
        or err_map.get('RuntimeError', [])
    )
    # TODO: For better information, we can raise an error with all error messages at one shot
    main_error = errors[0]
    return main_error


def _is_incorrect_multirow_spec(errors: List[Exception]) -> bool:
    return any('_InternalMultiSpec' in str(e) for e in errors)


def _extract_error(spec, failures: List[Tuple[bool, List[ValidateResult]]]) -> Exception:
    errors = []
    _flatten_results(failures, errors)
    err_mode = get_err_mode(spec)

    if _is_incorrect_multirow_spec(errors):
        msg = f'spec: {spec}, reason: incompatible data format for validation, an iterable object is needed'
        return ValueError(msg)

    if err_mode == ErrorMode.MSE:
        return _find_most_significant_error(errors)
    return DSVError(*errors)


def validate_data_spec(data, spec, **kwargs) -> bool:
    # SPEC validator as the root validator
    (_data, _spec) = repack_multirow(data, spec) if kwargs.get('multirow', False) else (data, spec)
    ok, failures = SpecValidator.validate(_data, {SpecValidator.name: _spec}, None)
    nothrow = kwargs.get('nothrow', False)

    if not ok and not nothrow:
        error = _extract_error(spec, failures)
        raise error
    return ok
