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
        import django  # noqa
    except ImportError:
        return False
    return True


def is_drf_installed():
    try:
        import rest_framework  # noqa
    except ImportError:
        return False
    return True


def make_request(cls, path='/', method='GET', user=None, headers=None, data=None, qs=None, is_json=False):
    assert is_django_installed()

    from django.core.handlers.asgi import ASGIRequest
    from django.core.handlers.wsgi import WSGIRequest

    if cls is not ASGIRequest:
        kwargs = {'REQUEST_METHOD': method, 'PATH_INFO': path, 'wsgi.input': StringIO()}
        if qs:
            kwargs.update({'QUERY_STRING': qs})

        # Set content type in initial environ if data is provided
        if data and method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            kwargs.update(
                {
                    'CONTENT_TYPE': 'application/json' if is_json else 'application/x-www-form-urlencoded',
                    'CONTENT_LENGTH': len(str(data)),
                }
            )

        req = WSGIRequest(kwargs)
    else:
        kwargs = {'path': path, 'method': method}
        if qs:
            kwargs.update({'query_string': qs})

        # Set content type in initial scope if data is provided
        if data and method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            headers = kwargs.get('headers', [])
            headers.extend(
                [
                    [
                        b'content-type',
                        ('application/json' if is_json else 'application/x-www-form-urlencoded').encode(),
                    ],
                    [b'content-length', str(len(str(data))).encode()],
                ]
            )
            kwargs['headers'] = headers

        req = ASGIRequest(kwargs, StringIO())

    req.user = user

    if headers:
        req.META.update(headers)

    if data:
        if method == 'GET':
            setattr(req, 'GET', data)
        elif method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            req.read()  # trigger RawPostDataException and force DRF to load data from req.POST
            if is_json:
                req._body = data
                req.POST = {}
            else:
                req.POST = data

    if is_drf_installed() and cls is not WSGIRequest and cls is not ASGIRequest:
        from rest_framework.parsers import FormParser
        from rest_framework.request import clone_request

        return clone_request(cls(req, parsers=[FormParser]), method)
    return req
