# data-spec-validator

## Why
* To get rid of code snippet like these (... cumbersome and tedious validation)
``` python
def do_something(params):
    val_a_must_int = params.get('a', 0)
    val_b_must_be_non_empty_list = params.get('b', [])
    # if key c presents, value c must be a date string between '2000-01-01' to '2020-01-01'
    val_c_might_be_none = params.get('c', None)

    # check type
    if type(val_a_must_int) != int:
      raise XXX

    # check type & value
    if type(val_b_must_list) != list or len(val_b_must_be_non_empty_list) == 0:
      raise XXX

    # if value exists, check its value
    if val_c_might_be_none is not None:
        date_c = datetime.strptime(val_c_might_be_present, '%Y-%m-%d')
        date_20000101 = datetime.date(2000, 1, 1)
        date_20200101 = datetime.date(2020, 1, 1)
        if not (date_20000101 <= date_c <= date_20200101):
          raise XXX
    ...
    # do something actually
```

## Installation
- Basic usage:
```shell
pip install data-spec-validator
```
- Advance usage (decorator)
  1. The decorator function `dsv` depends on `Django` & `djangorestframework`.
```shell
pip install data-spec-validator[decorator]
```

## Quick Example
* Do `validate_data_spec` directly wherever you like (see `test_spect.py` for more)
```python
from data_spec_validator.spec import INT, DIGIT_STR, ONE_OF, OPTIONAL, Checker, CheckerOP, validate_data_spec

class SomeSpec:
    field_a = Checker([INT])
    field_b = Checker([DIGIT_STR, OPTIONAL], op=CheckerOP.ANY)

some_data = dict(field_a=3, field_b='4', field_c=[1,2])
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


* Decorate a method with `dsv`, the method must meet one of the following requirements.
    1) Has a WSGIRequest(`django.core.handlers.wsgi.WSGIRequest`) attribute.
    2) The 2nd argument of the method is a `rest_framework.request.Request` instance.
```python
from rest_framework.views import APIView

from data_spec_validator.decorator import dsv
from data_spec_validator.spec import UUID, EMAIL, Checker

class SomeViewSpec:
  param_a = Checker([UUID])
  param_b = Checker([EMAIL])

class SomeView(APIView):
    @dsv(SomeViewSpec)
    def get(self, request):
        pass
```

### Register Custom Spec Check & Validator
- Define custom CHECK constant (`gt_check` in this case) and write custom Validator(`GreaterThanValidator` in this case)
```python
gt_check = 'gt_check'
from data_spec_validator.spec.defines import BaseValidator
class GreaterThanValidator(BaseValidator):
    name = gt_check

    @staticmethod
    def validate(value, extra, data):
        criteria = extra.get(GreaterThanValidator.name)
        return value > criteria, ValueError(f'{value} is not greater than {criteria}')
```
- Register custom check & validator into data_spec_validator
```python
from data_spec_validator.spec import custom_spec, Checker, validate_data_spec
custom_spec.register(dict(gt_check=GreaterThanValidator()))

class GreaterThanSpec:
    key = Checker([gt_check], extra={gt_check: 10})

ok_data = dict(key=11)
validate_data_spec(ok_data, GreaterThanSpec) # return True

nok_data = dict(key=9)
validate_data_spec(ok_data, GreaterThanSpec) # raise Exception
```

## Test
```bash
python -m unittest test.test_spec
```
