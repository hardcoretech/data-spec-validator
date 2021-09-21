import itertools
import unittest
from io import StringIO

from django.conf import settings
from parameterized import parameterized

from data_spec_validator.decorator import dsv, dsv_request_meta
from data_spec_validator.spec import DIGIT_STR, ONE_OF, Checker

settings.configure()

try:
    from django.core.handlers.wsgi import WSGIRequest
    from django.test import RequestFactory
    from django.views import View
    from rest_framework.exceptions import ParseError
    from rest_framework.parsers import FormParser
    from rest_framework.request import Request
except Exception:
    # To skip E402 module level import not at top of file
    pass


def _make_request(cls, path='/', method='GET', user=None, headers=None, data=None):
    assert cls in [WSGIRequest, Request]
    req = WSGIRequest({'REQUEST_METHOD': method, 'PATH_INFO': path, 'wsgi.input': StringIO()})

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

    return cls(req, parsers=[FormParser]) if cls == Request else req


def _make_django_view_params(req, kwargs=None):
    class DjangoView(View):
        request = req

    return (DjangoView(),), kwargs or {}


class TestDSV(unittest.TestCase):
    def test_should_check_name_url_params(self):
        # arrange
        class _ViewSpec:
            named_arg = Checker([DIGIT_STR])

        class _View(View):
            @dsv(_ViewSpec)
            def decorated_func(self, request, named_arg):
                pass

        factory = RequestFactory()
        req = factory.request()
        req = Request(req)
        view = _View()

        # action & assert
        view.decorated_func(req, named_arg='1')  # should pass validation

        with self.assertRaises(ParseError):
            view.decorated_func(req, named_arg='')

    def test_data_and_url_params_should_not_have_intersection(self):
        # arrange
        class _ViewSpec:
            pass

        class _View(View):
            @dsv(_ViewSpec)
            def decorated_func(self, request, named_arg):
                pass

        factory = RequestFactory()
        wsgi_req = factory.request()
        wsgi_req.GET = {'named_arg': ''}
        req = Request(wsgi_req)
        view = _View()

        # action & assert
        with self.assertRaises(RuntimeError):
            view.decorated_func(req, named_arg='')

    @parameterized.expand(itertools.product([dsv, dsv_request_meta], [Request, WSGIRequest], ['GET', 'POST']))
    def test_data_and_path_named_param_should_combine_together(self, dsv_deco, cls, method):
        # arrange
        payload = {'test_a': 'TEST A'}
        if dsv_deco == dsv:
            fake_request = _make_request(cls, method=method, data=payload)
        elif dsv_deco == dsv_request_meta:
            fake_request = _make_request(cls, method=method, headers=payload)

        kwargs = {'test_b': 'TEST_B'}

        class _ViewSpec:
            test_a = Checker([ONE_OF], extra={ONE_OF: 'TEST A'})
            test_b = Checker([ONE_OF], extra={ONE_OF: 'TEST_B'})

        class _View(View):
            @dsv_deco(_ViewSpec)
            def decorated_func(self, request, *_args, **_kwargs):
                pass

        view = _View(request=fake_request)
        view.decorated_func(fake_request, **kwargs)

    def test_non_view_request(self):
        # arrange
        class _NonViewSpec:
            field_a = Checker([DIGIT_STR])

        class _NonView:
            @dsv(_NonViewSpec)
            def decorated_func(self, request, field_a):
                pass

        factory = RequestFactory()
        req = factory.request()
        req = Request(req)
        non_view = _NonView()

        # action & assert
        non_view.decorated_func(req, field_a='1')  # should pass validation

        fake_args = ['1', '2', 3]
        with self.assertRaises(Exception):
            non_view.decorated_func(fake_args, field_a='1')


if __name__ == '__main__':
    unittest.main()
