import itertools
import unittest
from unittest.mock import patch

from parameterized import parameterized

from data_spec_validator.decorator import dsv, dsv_request_meta
from data_spec_validator.spec import DIGIT_STR, LIST_OF, ONE_OF, STR, Checker, dsv_feature

from .utils import is_django_installed, make_request

try:
    from django.conf import settings
    from django.core.handlers.wsgi import WSGIRequest
    from django.http import HttpResponse, HttpResponseBadRequest
    from django.test import RequestFactory
    from django.views import View

    settings.configure()
except Exception:
    # To skip E402 module level import not at top of file
    pass


@unittest.skipUnless(is_django_installed(), 'Django is not installed')
class TestDSVDJ(unittest.TestCase):
    def test_decorated_func_returns_error_response(self):
        # arrange
        class _ViewSpec:
            named_arg = Checker([DIGIT_STR])

        class _View(View):
            @dsv(_ViewSpec)
            def decorated_func(self, request, named_arg):
                return HttpResponse(status=200)

        factory = RequestFactory()
        req = factory.request()
        view = _View()

        # action
        resp_valid = view.decorated_func(req, named_arg='1')
        resp_invalid = view.decorated_func(req, named_arg='')

        # assert
        self.assertEqual(resp_valid.status_code, 200)
        self.assertEqual(resp_invalid.status_code, 400)

    def test_should_check_name_url_params(self):
        # arrange
        class _ViewSpec:
            named_arg = Checker([DIGIT_STR])

        class _View(View):
            @dsv(_ViewSpec)
            def decorated_func(self, request, named_arg):
                pass

        factory = RequestFactory()
        wsgi_req = factory.request()
        view = _View()

        # action & assert
        view.decorated_func(wsgi_req, named_arg='1')  # should pass validation

        resp = view.decorated_func(wsgi_req, named_arg='')
        assert isinstance(resp, HttpResponseBadRequest)

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
        view = _View()

        # action & assert
        with self.assertRaises(RuntimeError):
            view.decorated_func(wsgi_req, named_arg='')

    @parameterized.expand(itertools.product([dsv, dsv_request_meta], ['GET', 'POST']))
    def test_data_and_path_named_param_should_combine_together(self, dsv_deco, method):
        # arrange
        payload = {'test_a': 'TEST A'}
        if dsv_deco == dsv:
            fake_request = make_request(WSGIRequest, method=method, data=payload)
        elif dsv_deco == dsv_request_meta:
            fake_request = make_request(WSGIRequest, method=method, headers=payload)
        else:
            assert False

        kwargs = {'test_b': 'TEST_B'}

        class _ViewSpec:
            test_a = Checker([ONE_OF], ONE_OF='TEST A')
            test_b = Checker([ONE_OF], ONE_OF='TEST_B')

        class _View(View):
            @dsv_deco(_ViewSpec)
            def decorated_func(self, req, *_args, **_kwargs):
                pass

        view = _View(request=fake_request)
        view.decorated_func(fake_request, **kwargs)

    @parameterized.expand(['PUT', 'PATCH', 'DELETE'])
    def test_query_params_with_data(self, method):
        # arrange
        qs = 'q_a=3&q_b=true'
        payload = {'test_a': 'TEST A'}

        fake_request = make_request(WSGIRequest, method=method, data=payload, qs=qs)

        kwargs = {'test_b': 'TEST_B'}

        @dsv_feature(strict=True)
        class _ViewSpec:
            q_a = Checker([LIST_OF], LIST_OF=STR)
            q_b = Checker([LIST_OF], LIST_OF=STR)
            test_a = Checker([ONE_OF], ONE_OF='TEST A')
            test_b = Checker([ONE_OF], ONE_OF='TEST_B')

        class _View(View):
            @dsv(_ViewSpec)
            def decorated_func(self, req, *_args, **_kwargs):
                pass

        view = _View(request=fake_request)
        view.decorated_func(fake_request, **kwargs)

    def test_req_list_data_with_no_multirow_set(self):
        # arrange
        payload = [{'test_a': 'TEST A1'}, {'test_a': 'TEST A2'}, {'test_a': 'TEST A3'}]
        fake_request = make_request(WSGIRequest, method='POST', data=payload)
        kwargs = {'test_b': 'TEST_B'}

        class _ViewSingleRowSpec:
            test_a = Checker([STR])

        class _View(View):
            @dsv(_ViewSingleRowSpec)
            def decorated_func(self, request, *_args, **_kwargs):
                pass

        view = _View(request=fake_request)
        view.decorated_func(fake_request, **kwargs)

    def test_req_list_data_with_multirow_true(self):
        # arrange
        payload = [{'test_a': 'TEST A1'}, {'test_a': 'TEST A2'}, {'test_a': 'TEST A3'}]
        fake_request = make_request(WSGIRequest, method='POST', data=payload)
        kwargs = {'test_b': 'TEST_B'}

        class _ViewSingleRowSpec:
            test_a = Checker([STR])

        class _View(View):
            @dsv(_ViewSingleRowSpec, multirow=True)
            def decorated_func(self, request, *_args, **_kwargs):
                pass

        view = _View(request=fake_request)

        with patch('data_spec_validator.decorator.decorators._is_data_type_list', return_value=False):
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
        wsgi_req = factory.request()
        non_view = _NonView()

        # action & assert
        non_view.decorated_func(wsgi_req, field_a='1')  # should pass validation

        fake_args = ['1', '2', 3]
        with self.assertRaises(Exception):
            non_view.decorated_func(fake_args, field_a='1')


if __name__ == '__main__':
    unittest.main()
