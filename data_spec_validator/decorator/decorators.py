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


def _extract_request_info(req, **kwargs):
    assert _is_request(req), f'Unsupported req type, {type(req)}'

    def combine_params(_data, params):
        assert not (set(_data.keys()) & set(params.keys())), 'Data and URL named param have conflict'
        if isinstance(_data, QueryDict):
            qd = QueryDict(mutable=True)
            qd.update(_data)
            qd.update(params)
            return qd

        return {**_data, **params}

    if isinstance(req, WSGIRequest):
        assert req.method in ['GET', 'POST']
        data = req.GET if req.method == 'GET' else req.POST
    elif isinstance(req, Request):
        data = req.query_params if req.method == 'GET' else req.data
    else:
        assert False, 'Unexpected error here'

    # Named URL parameters should consider as params of the data spec.
    if type(data) == list:
        data = [combine_params(datum, kwargs) for datum in data]
    else:
        data = combine_params(data, kwargs)

    return data


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

            obj = args[0]
            if _is_request(obj):
                data = _extract_request_info(obj, **kwargs)
            elif _is_view(obj):
                if hasattr(obj, 'request') and isinstance(obj.request, WSGIRequest):
                    req = obj.request
                else:
                    assert len(args) >= 2, 'The decorated function must have at least 2 arguments'
                    req = args[1]
                data = _extract_request_info(req, **kwargs)
            else:
                assert False, 'Unexpected usage'

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

            return func(*args, **kwargs)

        return wrapped

    return wrapper
