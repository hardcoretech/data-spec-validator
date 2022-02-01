from .defines import MsgLv, UnknownFieldValue, ValidateResult, get_msg_level
from .validators import SpecValidator


def _wrap_error_with_field_info(failure) -> Exception:
    if get_msg_level() == MsgLv.VAGUE:
        return RuntimeError(f'field: {failure.field} not well-formatted')
    if isinstance(failure.value, UnknownFieldValue):
        return LookupError(f'field: {failure.field} missing')
    msg = f'field: {failure.field}, reason: {failure.error}'
    return type(failure.error)(msg)


def _flatten_results(failures, errors=None):
    if type(errors) != list:
        raise RuntimeError(f'{errors} not a list')

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


def _find_most_significant_error(failures) -> Exception:
    errors = []
    _flatten_results(failures, errors)

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
        else:
            err_key = 'RuntimeError'
        err_map.setdefault(err_key, []).append(err)

    # Severity, PermissionError > LookupError > TypeError > ValueError > RuntimeError.
    errors = (
        err_map.get('PermissionError', [])
        or err_map.get('LookupError', [])
        or err_map.get('TypeError', [])
        or err_map.get('ValueError', [])
        or err_map.get('RuntimeError', [])
    )
    # TODO: For better information, we can raise an error with all error messages at one shot
    main_error = errors[0]
    return main_error


def validate_data_spec(data, spec, **kwargs) -> bool:
    # SPEC validator as the root validator
    ok, failures = SpecValidator.validate(data, {SpecValidator.name: spec}, None)
    nothrow = kwargs.get('nothrow', False)

    if not ok and not nothrow:
        error = _find_most_significant_error(failures)
        raise error
    return ok
