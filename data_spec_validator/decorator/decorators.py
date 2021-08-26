from functools import wraps

try:
    import rest_framework.exceptions as drf_exceptions
    from django.core.handlers.wsgi import WSGIRequest
    from django.http import QueryDict
    from rest_framework.request import Request
except ModuleNotFoundError as e:
    print(f'[WARNING] decorator: "dsv" cannot be used, {e}')
from data_spec_validator.spec import validate_data_spec


def _extract_request_info(*args, **kwargs):
    def combine_params(_data, params):
        assert not (set(_data.keys()) & set(params.keys())), 'Data and URL named param have conflict'
        if isinstance(_data, QueryDict):
            qd = QueryDict(mutable=True)
            qd.update(_data)
            qd.update(params)
            return qd

        return {**_data, **params}

    view = args[0]
    if hasattr(view, 'request') and isinstance(view.request, WSGIRequest):
        # For report request
        req = view.request
        assert req.method in ['GET', 'POST']

        if req.method == 'GET':
            data = req.GET
        else:
            data = req.POST
    else:
        req = args[1]
        assert isinstance(req, Request)

        if not hasattr(view, 'bulk_create') or (
            hasattr(view, 'bulk_create') and (not view.bulk_create or req.method != 'POST')
        ):
            data = req.query_params if req.method == 'GET' else req.data
        else:
            # For CreateModelMixin.has_create_permission
            assert isinstance(args[2], list)
            data = args[2]

    # Named URL parameters should consider as params of the data spec.
    if type(data) == list:
        data = [combine_params(datum, kwargs) for datum in data]
    else:
        data = combine_params(data, kwargs)

    return data


def dsv(spec):
    """
    Used at
    For 1) APIView request method (get/post/put/patch/delete)
        2) |ListModelMixin.has_list_permission| & |RetrieveModelMixin.has_retrieve_permission| &
           |DestroyModelMixin.has_destroy_permission| & |UpdateModelMixin.has_update_permission| &
           & |CreateModelMixin.has_create_permission|
    NOTE: The 1st argument of the decorated function must be a django view instance
          which means the `self` object for a view's member function.
          And the 2nd argument is probably the request object.
    """

    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            data = _extract_request_info(*args, **kwargs)

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
