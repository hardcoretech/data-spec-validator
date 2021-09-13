from .defines import ValidateResult
from .validators import SpecValidator


def _wrap_error_with_field_info(failure):
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


def _find_most_significant_error(failures):
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
        else:
            err_key = 'RuntimeError'
        err_map.setdefault(err_key, []).append(err)

    # Severity, PermissionError > TypeError > ValueError > RuntimeError.
    errors = (
        err_map.get('PermissionError', [])
        or err_map.get('TypeError', [])
        or err_map.get('ValueError', [])
        or err_map.get('RuntimeError', [])
    )
    main_error = errors[0]
    return main_error


def validate_data_spec(data, spec, **kwargs):
    # SPEC validator as the root validator
    ok, failures = SpecValidator.validate(data, {SpecValidator.name: spec}, None)
    nothrow = kwargs.get('nothrow', False)

    if not ok and not nothrow:
        error = _find_most_significant_error(failures)
        raise error
    return ok
