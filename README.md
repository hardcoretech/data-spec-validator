# data-spec-validator

## Why
* TBD

## Quick Example
* Do `validate_data_spec` directly wherever you like (see `test_spect.py` for more)
```python
from spec import INT, DIGIT_STR, ONE_OF, OPTIONAL, Checker, CheckerOP, validate_data_spec

class SomeSpec:
    field_a = Checker([INT])
    field_b = Checker([DIGIT_STR, OPTIONAL], op=CheckerOP.ANY)

some_data = dict(field_a=3, field_b='4', field_c=list(1,2))
validate_data_spec(some_data, SomeSpec) # return True

some_data = dict(field_a=4)
validate_data_spec(some_data, SomeSpec) # return True

some_data = dict(field_a='3')
validate_data_spec(some_data, SomeSpec) # raise Exception

some_data = dict(field_a='3')
validate_data_spec(some_data, SomeSpec, nothrow=True) # return False

class AnotherSpec:
    field = Checker([ONE_OF], extra={ONE_OF: [1, '2', [3, 4], {'5': 6}]})

another_data = dict(field=[3, 4])
validate_data_spec(another_data, AnotherSpec) # return True

another_data = dict(field='4')
validate_data_spec(another_data, AnotherSpec) # raise Exception
```


* Decorate a method with `data_spec_validation`, the method must meet one of the following requirements.
    1) Has a WSGIRequest(`django.core.handlers.wsgi.WSGIRequest`) attribute.
    2) The 2nd argument of the method is a `rest_framework.request.Request` instance.
```python
from rest_framework.views import APIView

from decorators import data_spec_validation
from spec import UUID, EMAIL, Checker

class SomeViewSpec:
  param_a = Checker([UUID])
  param_b = Checker([EMAIL])

class SomeView(APIView):
    @data_spec_validation(SomeViewSpec)
    def get(self, request):
        pass
```

## Test
```bash
python -m unittest test.test_spec
```