import datetime
import unittest
import uuid

from data_spec_validator.spec import FOREACH, LIST_OF, Checker, validate_data_spec

from .utils import is_something_error


class TestBuiltinTypeSpec(unittest.TestCase):
    def test_int(self):
        class IntSpec:
            int_field = Checker([int])

        ok_data = dict(int_field=3)
        assert validate_data_spec(ok_data, IntSpec)

        nok_data = dict(int_field='3')
        assert is_something_error(TypeError, validate_data_spec, nok_data, IntSpec)

    def test_float(self):
        class FloatSpec:
            float_field = Checker([float])

        ok_data = dict(float_field=3.0)
        assert validate_data_spec(ok_data, FloatSpec)

        nok_data = dict(float_field=3)
        assert is_something_error(TypeError, validate_data_spec, nok_data, FloatSpec)

    def test_str(self):
        class StrSpec:
            str_field = Checker([str])

        ok_data = dict(str_field='3')
        assert validate_data_spec(ok_data, StrSpec)

        nok_data = dict(str_field=3)
        assert is_something_error(TypeError, validate_data_spec, nok_data, StrSpec)

    def test_none(self):
        class NoneSpec:
            none_field = Checker([type(None)])

        ok_data = dict(none_field=None)
        assert validate_data_spec(ok_data, NoneSpec)

        nok_data = dict(none_field=3)
        assert is_something_error(TypeError, validate_data_spec, nok_data, NoneSpec)

    def test_bool(self):
        class BoolSpec:
            bool_field = Checker([bool])

        ok_data = dict(bool_field=False)
        assert validate_data_spec(ok_data, BoolSpec)

        nok_data = dict(bool_field='True')
        assert is_something_error(TypeError, validate_data_spec, nok_data, BoolSpec)

    def test_list(self):
        class ListSpec:
            list_field = Checker([list])

        ok_data = dict(list_field=[1, 2, 3])
        assert validate_data_spec(ok_data, ListSpec)

        nok_data = dict(list_field=dict(a=2, b=4))
        assert is_something_error(TypeError, validate_data_spec, nok_data, ListSpec)

    def test_dict(self):
        class DictSpec:
            dict_field = Checker([dict])

        ok_data = dict(dict_field=dict(a=2, b=4))
        assert validate_data_spec(ok_data, DictSpec)

        nok_data = dict(dict_field=[1, 2, 3])
        assert is_something_error(TypeError, validate_data_spec, nok_data, DictSpec)

    def test_date_object(self):
        class DateObjSpec:
            date_object_field = Checker([datetime.date])

        ok_data = dict(date_object_field=datetime.date(2023, 2, 9))
        assert validate_data_spec(ok_data, DateObjSpec)

        nok_data = dict(date_object_field=datetime.datetime(2023, 2, 9, 12, 34))
        assert is_something_error(TypeError, validate_data_spec, nok_data, DateObjSpec)

    def test_datetime_object(self):
        class DatetimeObjSpec:
            datetime_object_field = Checker([datetime.datetime])

        ok_data = dict(datetime_object_field=datetime.datetime(2023, 2, 9, 12, 34))
        assert validate_data_spec(ok_data, DatetimeObjSpec)

        nok_data = dict(datetime_object_field=datetime.date(2023, 2, 9))
        assert is_something_error(TypeError, validate_data_spec, nok_data, DatetimeObjSpec)

    def test_uuid(self):
        class UuidSpec:
            uuid_field = Checker([uuid.UUID])

        uuid_inst = uuid.UUID('00000000-0000-0000-0000-000000000000')
        ok_data = dict(uuid_field=uuid_inst)
        assert validate_data_spec(ok_data, UuidSpec)

        nok_data = dict(uuid_field='z78ff51b-a354-4819-b2dd-bfaede3a8be5')
        assert is_something_error(TypeError, validate_data_spec, nok_data, UuidSpec)

    def test_iteration_of_types(self):
        class ListOfIntSpec:
            list_of_int_field = Checker([LIST_OF], LIST_OF=int)

        class ListOfStrSpec:
            list_of_str_field = Checker([LIST_OF], LIST_OF=str)

        class ForeachIntSpec:
            foreach_bool_field = Checker([FOREACH], FOREACH=bool)

        ok_data = dict(list_of_int_field=[3])
        assert validate_data_spec(ok_data, ListOfIntSpec)

        nok_data = dict(list_of_int_field=['3'])
        assert is_something_error(TypeError, validate_data_spec, nok_data, ListOfIntSpec)

        ok_data = dict(list_of_str_field=['3'])
        assert validate_data_spec(ok_data, ListOfStrSpec)

        nok_data = dict(list_of_str_field=[True])
        assert is_something_error(TypeError, validate_data_spec, nok_data, ListOfStrSpec)

        ok_data = dict(foreach_bool_field=[False])
        assert validate_data_spec(ok_data, ForeachIntSpec)

        nok_data = dict(foreach_bool_field=[3])
        assert is_something_error(TypeError, validate_data_spec, nok_data, ForeachIntSpec)
