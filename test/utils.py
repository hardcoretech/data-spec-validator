from io import StringIO


def is_something_error(error, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except error:
        return True
    return False


def is_type_error(func, *args):
    try:
        func(*args)
    except TypeError:
        return True
    return False


def is_django_installed():
    try:
        pass
    except ImportError:
        return False
    return True


def is_drf_installed():
    try:
        pass
    except ImportError:
        return False
    return True


def make_request(cls, path='/', method='GET', user=None, headers=None, data=None, qs=None):
    assert is_django_installed()
    kwargs = {'REQUEST_METHOD': method, 'PATH_INFO': path, 'wsgi.input': StringIO()}
    if qs:
        kwargs.update({'QUERY_STRING': qs})

    from django.core.handlers.wsgi import WSGIRequest

    req = WSGIRequest(kwargs)

    req.user = user

    if headers:
        req.META.update(headers)

    if data:
        if method == 'GET':
            setattr(req, 'GET', data)
        elif method == 'POST':
            req.read()  # trigger RawPostDataException and force DRF to load data from req.POST
            req.META.update(
                {
                    'CONTENT_TYPE': 'application/x-www-form-urlencoded',
                    'CONTENT_LENGTH': len(str(data)),
                }
            )
            req.POST = data

    if is_drf_installed() and cls is not WSGIRequest:
        from rest_framework.parsers import FormParser
        from rest_framework.request import clone_request

        return clone_request(cls(req, parsers=[FormParser]), method)
    return req
