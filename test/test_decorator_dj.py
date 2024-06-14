import itertools
import json
import unittest
from unittest.mock import patch

from parameterized import parameterized, parameterized_class

from data_spec_validator.decorator import dsv, dsv_request_meta
from data_spec_validator.decorator.decorators import ParseError
from data_spec_validator.spec import DIGIT_STR, LIST_OF, ONE_OF, STR, Checker, ErrorMode, dsv_feature

from .utils import is_django_installed, make_request

try:
    from django.conf import settings
    from django.core.handlers.asgi import ASGIRequest
    from django.core.handlers.wsgi import WSGIRequest
    from django.http import HttpResponse, JsonResponse
    from django.test import RequestFactory
    from django.views import View

    settings.configure()
except Exception:
    # To skip E402 module level import not at top of file
    pass


@parameterized_class(('request_class'), [(ASGIRequest,), (WSGIRequest,)])
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
                return HttpResponse(status=200)

        factory = RequestFactory()
        wsgi_req = factory.request()
        view = _View()

        # action & assert
        view.decorated_func(wsgi_req, named_arg='1')  # should pass validation

        resp = view.decorated_func(wsgi_req, named_arg='')
        self.assertIsInstance(resp, JsonResponse)
        self.assertEqual(resp.status_code, 400)

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
            fake_request = make_request(self.request_class, method=method, data=payload)
        elif dsv_deco == dsv_request_meta:
            fake_request = make_request(self.request_class, method=method, headers=payload)
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

    @parameterized.expand(itertools.product(['POST', 'PUT', 'PATCH', 'DELETE'], [True, False]))
    def test_query_params_with_data(self, method, is_json):
        # arrange
        qs = 'q_a=3&q_b=true&d.o.t=dot&array[]=a1&array[]=a2&array[]=a3'
        payload = {'test_a': 'TEST A', 'test_f[]': [1, 2, 3]}

        if is_json:
            payload = json.dumps(payload).encode('utf-8')
        fake_request = make_request(self.request_class, method=method, data=payload, qs=qs, is_json=is_json)

        kwargs = {'test_b': 'TEST_B', 'test_c.d.e': 'TEST C.D.E'}

        @dsv_feature(strict=True)
        class _ViewSpec:
            q_a = Checker([LIST_OF], LIST_OF=STR)
            q_b = Checker([LIST_OF], LIST_OF=STR)
            test_a = Checker([ONE_OF], ONE_OF='TEST A')
            test_b = Checker([ONE_OF], ONE_OF='TEST_B')
            test_c_d_e = Checker([ONE_OF], ONE_OF='TEST C.D.E', alias='test_c.d.e')
            test_f_array = Checker([LIST_OF], LIST_OF=int, alias='test_f[]')
            d_o_t = Checker([LIST_OF], LIST_OF=str, alias='d.o.t')
            array = Checker([LIST_OF], LIST_OF=str, alias='array[]')

        class _View(View):
            @dsv(_ViewSpec)
            def decorated_func(self, req, *_args, **_kwargs):
                return True

        view = _View(request=fake_request)
        assert view.decorated_func(fake_request, **kwargs)

    @parameterized.expand(['POST', 'PUT', 'PATCH', 'DELETE'])
    def test_query_params_with_data_in_invalid_json_format(self, method):
        payload = 'invalid json data'

        fake_request = make_request(self.request_class, method=method, data=payload, is_json=True)

        class _ViewSpec:
            pass

        class _View(View):
            @dsv(_ViewSpec)
            def decorated_func(self, req, *_args, **_kwargs):
                return True

        view = _View(request=fake_request)
        with self.assertRaises(ParseError):
            assert view.decorated_func(fake_request)

    def test_req_list_data_with_no_multirow_set(self):
        # arrange
        payload = [{'test_a': 'TEST A1'}, {'test_a': 'TEST A2'}, {'test_a': 'TEST A3'}]
        fake_request = make_request(self.request_class, method='POST', data=payload)
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
        fake_request = make_request(self.request_class, method='POST', data=payload)
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

    def test_json_response_content(self):
        # arrange
        @dsv_feature(err_mode=ErrorMode.ALL)
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
        resp_invalid = view.decorated_func(req, named_arg='hi')

        # assert
        self.assertIsInstance(resp_valid, HttpResponse)
        self.assertEqual(resp_valid.status_code, 200)

        self.assertIsInstance(resp_invalid, JsonResponse)
        self.assertEqual(resp_invalid.status_code, 400)
        self.assertEqual(
            json.loads(resp_invalid.content),
            {'messages': ["field: _ViewSpec.named_arg, reason: 'hi' is not a digit str"]},
        )


if __name__ == '__main__':
    unittest.main()
