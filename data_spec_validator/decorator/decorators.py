from functools import wraps

try:
    import rest_framework.exceptions as drf_exceptions
    from django.core.handlers.wsgi import WSGIRequest
    from django.http import QueryDict
    from django.views.generic.base import View
    from rest_framework.request import Request
except ModuleNotFoundError as e:
    print(f'[WARNING] decorator: "dsv" cannot be used, {e}')
from data_spec_validator.spec import validate_data_spec


def _is_request(obj):
    return isinstance(obj, WSGIRequest) or isinstance(obj, Request)


def _is_view(obj):
    return issubclass(type(obj), View)


def _combine_named_params(data, **kwargs):
    def combine_params(_data, params):
        if set(_data.keys()) & set(params.keys()):
            raise RuntimeError('Data and URL named param have conflict')

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
    if isinstance(req, WSGIRequest) or isinstance(req, Request):
        data = req.META
    else:
        raise Exception(f'Unsupported req type, {type(req)}')

    return _combine_named_params(data, **kwargs)


def _extract_request_param_data(req, **kwargs):
    if isinstance(req, WSGIRequest):
        if req.method not in ['GET', 'POST']:
            raise Exception(f'Disallowed method {req.method}')
        data = req.GET if req.method == 'GET' else req.POST
    elif isinstance(req, Request):
        data = req.query_params if req.method == 'GET' else req.data
    else:
        raise Exception(f'Unsupported req type, {type(req)}')

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
        if req:
            return req
        raise Exception('Unexpected usage')


def _do_validate(data, spec):
    # Raise DRF's exception to let DRF's exception handler do something about it.
    error = None
    try:
        if type(data) == list:
            for datum in data:
                validate_data_spec(datum, spec)
        else:
            validate_data_spec(data, spec)
    except ValueError as value_err:
        error = drf_exceptions.ValidationError(str(value_err.args))
    except PermissionError as perm_err:
        error = drf_exceptions.PermissionDenied(str(perm_err.args))
    except (TypeError, RuntimeError) as parse_err:
        error = drf_exceptions.ParseError(str(parse_err.args))

    if error:
        raise error


def dsv(spec):
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
            _do_validate(data, spec)
            return func(*args, **kwargs)

        return wrapped

    return wrapper


def dsv_request_meta(spec):
    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            req = _extract_request(*args)
            meta = _extract_request_meta(req, **kwargs)
            _do_validate(meta, spec)
            return func(*args, **kwargs)

        return wrapped

    return wrapper
