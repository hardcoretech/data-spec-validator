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
  1. The decorator function `dsv` may depend on `Django` or `djangorestframework`.
```shell
pip install data-spec-validator[decorator-dj]  # Django Only
pip install data-spec-validator[decorator]  # Django Rest Framework
```

## Quick Example
* Do `validate_data_spec` directly wherever you like
```python
from data_spec_validator.spec import INT, DIGIT_STR, ONE_OF, Checker, CheckerOP, validate_data_spec

class SomeSpec:
    field_a = Checker([INT])
    field_b = Checker([DIGIT_STR], optional=True)
    field_c = Checker([DIGIT_STR, INT], op=CheckerOP.ANY)

some_data = dict(field_a=4, field_b='3', field_c=1, field_dont_care=[5,6])
validate_data_spec(some_data, SomeSpec) # return True

some_data = dict(field_a=4, field_c='1')
validate_data_spec(some_data, SomeSpec) # return True

some_data = dict(field_a=4, field_c=1)
validate_data_spec(some_data, SomeSpec) # return True

some_data = dict(field_a='4', field_c='1')
validate_data_spec(some_data, SomeSpec) # raise Exception

some_data = dict(field_a='4', field_c='1')
validate_data_spec(some_data, SomeSpec, nothrow=True) # return False

class AnotherSpec:
    field = Checker([ONE_OF], ONE_OF=[1, '2', [3, 4], {'5': 6}])

another_data = dict(field=[3, 4])
validate_data_spec(another_data, AnotherSpec) # return True

another_data = dict(field='4')
validate_data_spec(another_data, AnotherSpec) # raise Exception
```

* Multiple rows data
```python
from data_spec_validator.spec import INT, STR, Checker, validate_data_spec

class SingleSpec:
    f_a = Checker([INT])
    f_b = Checker([STR])

multirow_data = [dict(f_a=1, f_b='1'), dict(f_a=2, f_b='2'), dict(f_a=3, f_b='3')]
validate_data_spec(multirow_data, SingleSpec, multirow=True) # return True

```


---
## Supported checks & sample usages (see `test_spec.py`/`test_class_type_spec.py` for more cases)

### INT
`int_field = Checker([INT])` or `Checker[int]`

### FLOAT
`float_field = Checker([FLOAT])` or `Checker([float])`

### STR
`str_field = Checker([STR])` or `Checker([str])`

### DIGIT_STR
`digi_str_field = Checker([DIGIT_STR])`

### BOOL
`bool_field = Checker([BOOL])` or `Checker([bool])`

### DICT
`dict_field = Checker([DICT])` or `Checker([dict])`

### LIST
`list_field = Checker([LIST])` or `Checker([list])`

### DATE_OBJECT
`date_obj_field = Checker([DATE_OBJECT])` or `Checker([datetime.date])`

### DATETIME_OBJECT
`datetime_obj_field = Checker([DATETIME_OBJECT])` or `Checker([datetime.datetime])`

### NONE
`none_field = Checker([NONE])` or `Checker([type(None)])`

### JSON
`json_field = Checker([JSON])`

### JSON_BOOL
`json_bool_field = Checker([JSON_BOOL])`

### ONE_OF
`one_of_field = Checker([ONE_OF], ONE_OF=['a', 'b', 'c'])`

### SPEC
`spec_field = Checker([SPEC], SPEC=SomeSpecClass)`

### LIST_OF: Enforce LIST type validation as well
`list_of_int_field = Checker([LIST_OF], LIST_OF=INT)`

`list_of_spec_field = Checker([LIST_OF], LIST_OF=SomeSpecClass)`

### LENGTH
`length_field = Checker([LENGTH], LENGTH=dict(min=3, max=5))`

### AMOUNT
`amount_field = Checker([AMOUNT])`

### AMOUNT_RANGE
`amount_range_field = Checker([AMOUNT_RANGE], AMOUNT_RANGE=dict(min=-2.1, max=3.8))`

### DECIMAL_PLACE
`decimal_place_field = Checker([DECIMAL_PLACE], DECIMAL_PLACE=4)`

### DATE
`date_field = Checker([DATE])`

### DATE_RANGE
`date_range_field = Checker([DATE_RANGE], DATE_RANGE=dict(min='2000-01-01', max='2010-12-31'))`

### EMAIL
`email_field = Checker([EMAIL])`

### UUID
`uuid_field = Checker([UUID])` or `Checker([uuid.UUID])`

### REGEX
`re_field = Checker([REGEX], REGEX=dict(pattern=r'^The'))`

`re_field = Checker([REGEX], REGEX=dict(pattern=r'watch out', method='match'))`

### COND_EXIST
If a exists, c must not exist, if b exists, a must exist, if c exists, a must not exist.

Practically, `optional=True` will be configured in the most use cases, FMI, see `test/test_spec.py`

`a = Checker([COND_EXIST], optional=True, COND_EXIST=dict(WITHOUT=['c']))`

`b = Checker([COND_EXIST], optional=True, COND_EXIST=dict(WITH=['a']))`

`c = Checker([COND_EXIST], optional=True, COND_EXIST=dict(WITHOUT=['a']))`

### Self-defined class type
```
class SomeClass:
    pass

a = Checker([SomeClass])
```

---

* Decorate a method with `dsv`, the method must meet one of the following requirements.
    1) It's a view's member function, and the view has a WSGIRequest(`django.core.handlers.wsgi.WSGIRequest`) attribute.
    2) It's a view's member function, and the 2nd argument of the method is a `rest_framework.request.Request` instance.
    3) It's already decorated with `rest_framework.decorators import api_view`, the 1st argument is a `rest_framework.request.Request`
```python
from rest_framework.decorators import api_view
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

@api_view(('POST',))
@dsv(SomeViewSpec)
def customer_create(request):
    pass

@api_view(('POST',))
@dsv(SomeViewSpec, multirow=True)  # For type(request.POST) is list
def customer_create(request):
    pass
```

* Decorate another method with `dsv_request_meta` can help you validate the META in request header.
---

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
    key = Checker(['gt_check'], GT_CHECK=10)

ok_data = dict(key=11)
validate_data_spec(ok_data, GreaterThanSpec) # return True

nok_data = dict(key=9)
validate_data_spec(ok_data, GreaterThanSpec) # raise Exception
```
---
### Message Level

- 2 modes (**Default** v.s. **Vague**), can be switched by calling `reset_msg_level(vague=True)`
```python
# In default mode, any exception happens, there will be a reason in the message
"field: XXX, reason: '3' is not a integer"

# In vague mode, any exception happens, a general message is shown
"field: XXX not well-formatted"
```
---
### Feature: Strict Mode

- A spec class decorated with `dsv_feature(strict=True)` detects unexpected key/value in data
```python
from data_spec_validator.spec import Checker, validate_data_spec, dsv_feature, BOOL

@dsv_feature(strict=True)
class StrictSpec:
    a = Checker([BOOL])

ok_data = dict(a=True)
validate_data_spec(ok_data, StrictSpec) # return True

nok_data = dict(a=True, b=1)
validate_data_spec(nok_data, StrictSpec) # raise Exception
```
---
### Feature: Any Keys Set

- A spec class decorated with e.g. `dsv_feature(any_keys_set={...})` means that at least one key among a keys tuple from the set must exist.
```python
from data_spec_validator.spec import Checker, validate_data_spec, dsv_feature, INT

@dsv_feature(any_keys_set={('a', 'b'), ('c', 'd')})
class _AnyKeysSetSpec:
    a = Checker([INT], optional=True)
    b = Checker([INT], optional=True)
    c = Checker([INT], optional=True)
    d = Checker([INT], optional=True)

validate_data_spec(dict(a=1, c=1, d=1), _AnyKeysSetSpec)
validate_data_spec(dict(a=1, c=1), _AnyKeysSetSpec)
validate_data_spec(dict(a=1, d=1), _AnyKeysSetSpec)
validate_data_spec(dict(b=1, c=1, d=1), _AnyKeysSetSpec)
validate_data_spec(dict(b=1, c=1), _AnyKeysSetSpec)
validate_data_spec(dict(b=1, d=1), _AnyKeysSetSpec)
validate_data_spec(dict(a=1, b=1, c=1), _AnyKeysSetSpec)
validate_data_spec(dict(a=1, b=1, d=1), _AnyKeysSetSpec)
validate_data_spec(dict(a=1, b=1, c=1, d=1), _AnyKeysSetSpec)

validate_data_spec(dict(a=1), _AnyKeysSetSpec) # raise exception
validate_data_spec(dict(b=1), _AnyKeysSetSpec) # raise exception
validate_data_spec(dict(c=1), _AnyKeysSetSpec) # raise exception
validate_data_spec(dict(d=1), _AnyKeysSetSpec) # raise exception
validate_data_spec(dict(e=1), _AnyKeysSetSpec) # raise exception
```
---
### Feature: Error Mode, i.e. ErrorMode.ALL, ErrorMode.MSE(default behavior)
NOTE 1: `ErrorMode.MSE` stands for MOST-SIGNIFICANT-ERROR

NOTE 2: The validation results respect to the ErrorMode feature config on the **OUTER-MOST** spec. All nested specs
        follow the **OUTER-MOST** spec configuration, for more reference, see `test_spec.py:test_err_mode`
```python
from data_spec_validator.spec import Checker, validate_data_spec, dsv_feature, LENGTH, STR, AMOUNT, ErrorMode, INT, DIGIT_STR

@dsv_feature(err_mode=ErrorMode.ALL)
class _ErrModeAllSpec:
    a = Checker([INT])
    b = Checker([DIGIT_STR])
    c = Checker([LENGTH, STR, AMOUNT], LENGTH=dict(min=3, max=5))

nok_data = dict(
    a=True,
    b='abc',
    c='22',
)

validate_data_spec(nok_data, _ErrModeAllSpec) # raise DSVError
"""
A DSVError is raised with 3 errors in args.
(TypeError('field: _ErrModeAllSpec.a, reason: True is not an integer',),
 TypeError("field: _ErrModeAllSpec.b, reason: 'abc' is not a digit str",),
 ValueError("field: _ErrModeAllSpec.c, reason: Length of '22' must be between 3 and 5",))

"""
```

---
## Test
```bash
python -m unittest test/*.*
```
