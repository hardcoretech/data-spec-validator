from functools import wraps
from typing import Dict, List, Union

from data_spec_validator.spec import DSVError, raise_if, validate_data_spec

try:
    from django.core.handlers.wsgi import WSGIRequest
    from django.http import HttpResponseBadRequest, HttpResponseForbidden, QueryDict
    from django.views.generic.base import View
except ModuleNotFoundError as e:
    print(f'[DSV][WARNING] decorator: "dsv" cannot be used, {e}')

_enabled_drf = False
try:
    import rest_framework.exceptions as drf_exceptions
    from rest_framework.request import Request

    _enabled_drf = True
except ModuleNotFoundError:
    print('[DSV][INFO] decorator: using "dsv" without djangorestframework')


class ValidationError(Exception):
    def __init__(self, message):
        self.message = message


class PermissionDenied(Exception):
    def __init__(self, message):
        self.message = message


class ParseError(Exception):
    def __init__(self, message):
        self.message = message


def _is_wsgi_request(obj):
    return isinstance(obj, WSGIRequest)


def _is_drf_request(obj):
    return _enabled_drf and isinstance(obj, Request)


def _is_request(obj):
    return _is_wsgi_request(obj) or _is_drf_request(obj)


def _is_view(obj):
    return issubclass(type(obj), View)


def _combine_named_params(data, **kwargs):
    def combine_params(_data, params):

        raise_if(bool(set(_data.keys()) & set(params.keys())), RuntimeError('Data and URL named param have conflict'))

        if isinstance(_data, QueryDict):
            qd = QueryDict(mutable=True)
            qd.update(_data)
            qd.update(params)
            return qd

        return {**_data, **params}

    # Named URL parameters should consider as params of the data spec.
    if type(data) == list:
        data = [combine_params(datum, kwargs) for datum in data]
    else:
        data = combine_params(data, kwargs)
    return data


def _extract_request_meta(req, **kwargs):
    raise_if(
        not _is_wsgi_request(req) and not _is_drf_request(req),
        RuntimeError(f'Unsupported req type, {type(req)}'),
    )
    return _combine_named_params(req.META, **kwargs)


def _extract_request_param_data(req, **kwargs):
    is_wsgi_request = _is_wsgi_request(req)
    is_request = _is_drf_request(req)
    raise_if(
        not is_wsgi_request and not is_request,
        RuntimeError(f'Unsupported req type, {type(req)}'),
    )

    def _collect_data(method, req_qp, req_data) -> Dict:
        if method == 'GET':
            return req_qp
        else:
            if req_qp and issubclass(type(req_qp), dict) and type(req_data) is not list:
                return {**req_qp, **req_data}
            # TODO: Don't care about the query_params if it's not a dict or the payload is in list.
            return req_data

    if is_wsgi_request:
        data = _collect_data(req.method, req.GET, req.POST)
    else:
        data = _collect_data(req.method, req.query_params, req.data)

    return _combine_named_params(data, **kwargs)


def _extract_request(*args):
    obj = args[0]
    if _is_request(obj):
        return obj
    elif hasattr(obj, 'request') and _is_request(obj.request):
        return obj.request
    else:
        # Fallback to find the first request object
        req = next(filter(lambda o: _is_request(o), args), None)
        raise_if(not req, RuntimeError('Unexpected usage'))
        return req


def _is_data_type_list(data: Union[Dict, List]) -> bool:
    return type(data) == list


def _eval_is_multirow(multirow: bool, data: Union[Dict, List]) -> bool:
    # NOTE: is_multirow by evaluating list type will be deprecated, so the client must specify multirow=True
    #       explicitly in the future.
    return multirow or _is_data_type_list(data)


def _do_validate(data, spec, multirow):
    # Raise exceptions with message if validation failed.
    error = None
    try:
        is_multirow = _eval_is_multirow(multirow, data)
        validate_data_spec(data, spec, multirow=is_multirow)
    except ValueError as value_err:
        error = ValidationError(str(value_err.args))
    except PermissionError as perm_err:
        error = PermissionDenied(str(perm_err.args))
    except (LookupError, TypeError, RuntimeError, DSVError) as parse_err:
        error = ParseError(str(parse_err.args))

    if error:
        raise error


def _get_error_response(error, use_drf):
    """
    Return the error response based on the error type.
    If the attribute use_drf is True, Raise DRF's exception to let DRF's exception handler do something about it.
    """
    if use_drf:
        err_map = {
            ValidationError: drf_exceptions.ValidationError,
            PermissionDenied: drf_exceptions.PermissionDenied,
            ParseError: drf_exceptions.ParseError,
        }
        raise err_map[error.__class__](error.message)

    resp_map = {
        ValidationError: HttpResponseBadRequest,
        PermissionDenied: HttpResponseForbidden,
        ParseError: HttpResponseBadRequest,
    }
    return resp_map[error.__class__](error.message)


def dsv(spec, multirow=False):
    """
    Used at any function where view instance or request is the first argument.
    e.g. 1) APIView request method (get/post/put/patch/delete)
         2) |ListModelMixin.has_list_permission| & |RetrieveModelMixin.has_retrieve_permission| &
            |DestroyModelMixin.has_destroy_permission| & |UpdateModelMixin.has_update_permission| &
            & |CreateModelMixin.has_create_permission (NOTE: bulk_create must be False)|
    """

    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            req = _extract_request(*args)
            data = _extract_request_param_data(req, **kwargs)

            try:
                _do_validate(data, spec, multirow)
            except (ValidationError, PermissionDenied, ParseError) as err:
                return _get_error_response(err, use_drf=_is_drf_request(req))

            return func(*args, **kwargs)

        return wrapped

    return wrapper


def dsv_request_meta(spec):
    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            req = _extract_request(*args)
            meta = _extract_request_meta(req, **kwargs)

            try:
                _do_validate(meta, spec, multirow=False)
            except (ValidationError, PermissionDenied, ParseError) as err:
                return _get_error_response(err, use_drf=_is_drf_request(req))

            return func(*args, **kwargs)

        return wrapped

    return wrapper
