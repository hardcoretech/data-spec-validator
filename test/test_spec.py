import datetime
import unittest
import uuid
from datetime import date
from itertools import chain

from data_spec_validator.spec import (
    AMOUNT,
    AMOUNT_RANGE,
    BOOL,
    COND_EXIST,
    DATE,
    DATE_OBJECT,
    DATE_RANGE,
    DATETIME_OBJECT,
    DECIMAL_PLACE,
    DICT,
    DIGIT_STR,
    EMAIL,
    FLOAT,
    FOREACH,
    INT,
    JSON,
    JSON_BOOL,
    LENGTH,
    LIST,
    LIST_OF,
    NONE,
    ONE_OF,
    REGEX,
    SELF,
    SPEC,
    STR,
    UUID,
    Checker,
    CheckerOP,
    DSVError,
    ErrorMode,
    dsv_feature,
    not_,
    reset_msg_level,
    validate_data_spec,
)
from data_spec_validator.spec.validators import BaseValidator

from .utils import is_something_error, is_type_error


class TestSpec(unittest.TestCase):
    def test_int(self):
        class IntSpec:
            int_field = Checker([INT])

        ok_data = dict(int_field=3)
        assert validate_data_spec(ok_data, IntSpec)

        nok_data = dict(int_field='3')
        assert is_something_error(TypeError, validate_data_spec, nok_data, IntSpec)

    def test_float(self):
        class FloatSpec:
            float_field = Checker([FLOAT])

        ok_data = dict(float_field=3.0)
        assert validate_data_spec(ok_data, FloatSpec)

        nok_data = dict(float_field=3)
        assert is_something_error(TypeError, validate_data_spec, nok_data, FloatSpec)

    def test_str(self):
        class StrSpec:
            str_field = Checker([STR])

        ok_data = dict(str_field='3')
        assert validate_data_spec(ok_data, StrSpec)

        nok_data = dict(str_field=3)
        assert is_something_error(TypeError, validate_data_spec, nok_data, StrSpec)

    def test_none(self):
        class NoneSpec:
            none_field = Checker([NONE])

        ok_data = dict(none_field=None)
        assert validate_data_spec(ok_data, NoneSpec)

        nok_data = dict(none_field=3)
        assert is_something_error(TypeError, validate_data_spec, nok_data, NoneSpec)

    def test_allow_none(self):
        class AllowNoneSpec:
            maybe_none_field = Checker([INT], allow_none=True)

        ok_data = dict(maybe_none_field=3)
        assert validate_data_spec(ok_data, AllowNoneSpec)

        ok_data = dict(maybe_none_field=None)
        assert validate_data_spec(ok_data, AllowNoneSpec)

        nok_data = dict(maybe_none_field='3')
        assert is_something_error(TypeError, validate_data_spec, nok_data, AllowNoneSpec)

    def test_bool(self):
        class BoolSpec:
            bool_field = Checker([BOOL])

        ok_data = dict(bool_field=False)
        assert validate_data_spec(ok_data, BoolSpec)

        nok_data = dict(bool_field='True')
        assert is_something_error(TypeError, validate_data_spec, nok_data, BoolSpec)

    def test_self(self):
        class SelfSpec:
            next_field = Checker([SPEC], optional=True, SPEC=SELF)
            children = Checker([LIST_OF], optional=True, LIST_OF=SPEC, SPEC=SELF)

        ok_data = dict(
            next_field=dict(
                next_field=dict(
                    next_field=dict(),
                ),
            ),
            children=[
                dict(
                    next_field=dict(next_field=dict()),
                ),
                dict(
                    next_field=dict(),
                ),
                dict(
                    children=[dict()],
                ),
            ],
        )
        assert validate_data_spec(ok_data, SelfSpec)

        nok_data = dict(next_field=dict(next_field=0))
        assert is_something_error(Exception, validate_data_spec, nok_data, SelfSpec)

    def test_list(self):
        class ListSpec:
            list_field = Checker([LIST])

        ok_data = dict(list_field=[1, 2, 3])
        assert validate_data_spec(ok_data, ListSpec)

        nok_data = dict(list_field=dict(a=2, b=4))
        assert is_something_error(TypeError, validate_data_spec, nok_data, ListSpec)

    def test_dict(self):
        class DictSpec:
            dict_field = Checker([DICT])

        ok_data = dict(dict_field=dict(a=2, b=4))
        assert validate_data_spec(ok_data, DictSpec)

        nok_data = dict(dict_field=[1, 2, 3])
        assert is_something_error(TypeError, validate_data_spec, nok_data, DictSpec)

    def test_date_object(self):
        class DateObjSpec:
            date_object_field = Checker([DATE_OBJECT])

        ok_data = dict(date_object_field=datetime.date(2023, 2, 9))
        assert validate_data_spec(ok_data, DateObjSpec)

        nok_data = dict(date_object_field=datetime.datetime(2023, 2, 9, 12, 34))
        assert is_something_error(TypeError, validate_data_spec, nok_data, DateObjSpec)

    def test_datetime_object(self):
        class DatetimeObjSpec:
            datetime_object_field = Checker([DATETIME_OBJECT])

        ok_data = dict(datetime_object_field=datetime.datetime(2023, 2, 9, 12, 34))
        assert validate_data_spec(ok_data, DatetimeObjSpec)

        nok_data = dict(datetime_object_field=datetime.date(2023, 2, 9))
        assert is_something_error(TypeError, validate_data_spec, nok_data, DatetimeObjSpec)

    def test_optional(self):
        class OptionalSpec:
            optional_field = Checker([STR], optional=True)

        ok_data = dict(whatever_field='dont_care')
        assert validate_data_spec(ok_data, OptionalSpec)

    def test_amount(self):
        class AmountSpec:
            amount_field = Checker([AMOUNT])

        ok_data = dict(amount_field='3.1415')
        assert validate_data_spec(ok_data, AmountSpec)

        ok_data = dict(amount_field=5566)
        assert validate_data_spec(ok_data, AmountSpec)

        nok_data = dict(amount_field='abc')
        assert is_something_error(ValueError, validate_data_spec, nok_data, AmountSpec)

    def test_amount_range(self):
        class AmountRangeSpec:
            amount_range_field = Checker([AMOUNT_RANGE], AMOUNT_RANGE=dict(min=-2.1, max=3.8))

        ok_data = dict(
            amount_range_field='3.8',
        )
        assert validate_data_spec(ok_data, AmountRangeSpec)

        ok_data = dict(amount_range_field=-2.1)
        assert validate_data_spec(ok_data, AmountRangeSpec)

        nok_data = dict(amount_range_field='-2.2')
        assert is_something_error(ValueError, validate_data_spec, nok_data, AmountRangeSpec)

        nok_data = dict(amount_range_field='3.81')
        assert is_something_error(ValueError, validate_data_spec, nok_data, AmountRangeSpec)

    def test_length(self):
        class LengthSpec:
            length_field = Checker([LENGTH], LENGTH=dict(min=3, max=5))

        ok_data = dict(length_field='3.2')
        assert validate_data_spec(ok_data, LengthSpec)

        ok_data = dict(length_field='3.141')
        assert validate_data_spec(ok_data, LengthSpec)

        nok_data = dict(length_field='ah')
        assert is_something_error(ValueError, validate_data_spec, nok_data, LengthSpec)

        nok_data = dict(length_field='exceed')
        assert is_something_error(ValueError, validate_data_spec, nok_data, LengthSpec)

    def test_decimal_place(self):
        class DecimalPlaceSpec:
            decimal_place_field = Checker([DECIMAL_PLACE], DECIMAL_PLACE=4)

        ok_data = dict(decimal_place_field=3.123)
        assert validate_data_spec(ok_data, DecimalPlaceSpec)

        ok_data = dict(decimal_place_field=3.1234)
        assert validate_data_spec(ok_data, DecimalPlaceSpec)

        nok_data = dict(decimal_place_field=3.12345)
        assert is_something_error(ValueError, validate_data_spec, nok_data, DecimalPlaceSpec)

    def test_date(self):
        class DateStrSpec:
            date_field = Checker([DATE])

        ok_data = dict(date_field='2000-01-31')
        assert validate_data_spec(ok_data, DateStrSpec)

        ok_data = dict(date_field='1-31-2000')
        assert validate_data_spec(ok_data, DateStrSpec)

        ok_data = dict(date_field='20200101')
        assert validate_data_spec(ok_data, DateStrSpec)

        nok_data = dict(date_field='202011')
        assert is_something_error(ValueError, validate_data_spec, nok_data, DateStrSpec)

    def test_date_range(self):
        class DateStrRangeSpec:
            date_range_field = Checker(
                [DATE_RANGE],
                DATE_RANGE=dict(min='2000-01-01', max='2010-12-31'),
            )

        ok_data = dict(date_range_field='2000-1-1')
        assert validate_data_spec(ok_data, DateStrRangeSpec)

        ok_data = dict(date_range_field='2005-12-31')
        assert validate_data_spec(ok_data, DateStrRangeSpec)

        ok_data = dict(date_range_field='2010-12-31')
        assert validate_data_spec(ok_data, DateStrRangeSpec)

        nok_data = dict(date_range_field='1999-12-31')
        assert is_something_error(ValueError, validate_data_spec, nok_data, DateStrRangeSpec)

    def test_nested_spec(self):
        class LeafSpec:
            int_field = Checker([INT])
            str_field = Checker([STR])
            bool_field = Checker([BOOL])

        class MidLeafSpec:
            int_field = Checker([INT])
            str_field = Checker([STR])
            leaf_field = Checker([SPEC], SPEC=LeafSpec)

        class RootSpec:
            int_field = Checker([INT])
            mid_leaf_field = Checker([SPEC], SPEC=MidLeafSpec)
            bool_field = Checker([BOOL])

        ok_data = dict(
            int_field=1,
            mid_leaf_field=dict(
                int_field=2,
                str_field='2',
                leaf_field=dict(
                    int_field=3,
                    str_field='3',
                    bool_field=True,
                ),
            ),
            bool_field=False,
        )
        assert validate_data_spec(ok_data, RootSpec)

        nok_data = dict(
            int_field=1,
            mid_leaf_field=dict(
                int_field=2,
                wrong_name_mid_field='2',
                leaf_field=dict(
                    int_field=3,
                    str_field='3',
                    bool_field=True,
                ),
            ),
            bool_field=False,
        )
        assert is_something_error(LookupError, validate_data_spec, nok_data, RootSpec)

        nok_data = dict(
            int_field=1,
            mid_leaf_field=dict(
                int_field=2,
                str_field='2',
                leaf_field=dict(
                    int_field=3,
                    str_field='3',
                    wrong_name_leaf_field=True,
                ),
            ),
            bool_field=False,
        )
        assert is_something_error(LookupError, validate_data_spec, nok_data, RootSpec)

    def test_list_of(self):
        class ChildSpec:
            int_field = Checker([INT])
            bool_field = Checker([BOOL])

        class ParentSpec:
            list_of_spec_field = Checker([LIST_OF], LIST_OF=SPEC, SPEC=ChildSpec)

        ok_data = dict(
            list_of_spec_field=[
                dict(int_field=1, bool_field=False),
                dict(int_field=2, bool_field=True),
                dict(int_field=3, bool_field=False),
            ]
        )
        assert validate_data_spec(ok_data, ParentSpec)

        nok_data = dict(
            list_of_spec_field=[
                dict(int_field=1, bool_field=False),
                2,
            ]
        )
        assert is_something_error(TypeError, validate_data_spec, nok_data, ParentSpec)

        class ListOfIntSpec:
            list_of_int_field = Checker([LIST_OF], LIST_OF=INT)

        ok_data = dict(list_of_int_field=[1, 2, 3])
        assert validate_data_spec(ok_data, ListOfIntSpec)

        nok_with_non_list_data = dict(list_of_int_field={1: 1, 2: 2, 3: 3})
        assert is_something_error(TypeError, validate_data_spec, nok_with_non_list_data, ListOfIntSpec)

        nok_data = dict(list_of_int_field=[1, 2, '3'])
        assert is_something_error(TypeError, validate_data_spec, nok_data, ListOfIntSpec)

    def test_foreach(self):
        class ChildSpec:
            int_field = Checker([INT])
            bool_field = Checker([BOOL])

        class ParentSpec:
            foreach_spec_field = Checker([FOREACH], FOREACH=SPEC, SPEC=ChildSpec)

        ok_data = dict(
            foreach_spec_field=(
                dict(int_field=1, bool_field=False),
                dict(int_field=2, bool_field=True),
                dict(int_field=3, bool_field=False),
            )
        )
        assert validate_data_spec(ok_data, ParentSpec)

        class ForeachIntSpec:
            foreach_spec_field = Checker([FOREACH], FOREACH=INT)

        ok_data = dict(foreach_spec_field=(1, 2, 3))
        assert validate_data_spec(ok_data, ForeachIntSpec)
        ok_data = dict(foreach_spec_field=[1, 2, 3])
        assert validate_data_spec(ok_data, ForeachIntSpec)
        ok_data = dict(foreach_spec_field={1, 2, 3})
        assert validate_data_spec(ok_data, ForeachIntSpec)
        ok_data = dict(foreach_spec_field={1: 1, 2: 2, 3: 3})
        assert validate_data_spec(ok_data, ForeachIntSpec)

    def test_one_of(self):
        class OneOfSpec:
            one_of_spec_field = Checker([ONE_OF], ONE_OF=[1, '2', [3, 4], {'5': 6}])

        ok_data = dict(one_of_spec_field=1)
        assert validate_data_spec(ok_data, OneOfSpec)

        ok_data = dict(one_of_spec_field='2')
        assert validate_data_spec(ok_data, OneOfSpec)

        ok_data = dict(one_of_spec_field=[3, 4])
        assert validate_data_spec(ok_data, OneOfSpec)

        ok_data = dict(one_of_spec_field={'5': 6})
        assert validate_data_spec(ok_data, OneOfSpec)

        nok_data = dict(one_of_spec_field=6)
        assert is_something_error(ValueError, validate_data_spec, nok_data, OneOfSpec)

    def test_json(self):
        class JsonSpec:
            json_spec_field = Checker([JSON])

        for value in chain.from_iterable(
            (
                ('-1', '0', '3.14', '2.718e-4'),  # Numbers
                ('"Hello"', "\"World\""),  # Strings
                ('false', 'true'),  # Booleans
                ('[]', '[0, 1, 2]', '[1, "+", 1, "=", 2]'),  # Arrays
                ('{}', '{"foo":"bar"}', '{"sheldon":["says","bazinga"]}'),  # Objects
                ('null',),  # null
            )
        ):
            ok_data = dict(json_spec_field=value)
            assert validate_data_spec(ok_data, JsonSpec), value

        for value in chain.from_iterable(
            (
                ('0123', '0xFFFF'),  # Numbers
                ('Hello', "'World'"),  # Strings
                ('False', 'TRUE'),  # Booleans
                ('(1, 2, 3)',),  # Arrays
                ('{foo:"bar"}', '{"foo":"bar",}'),  # Objects
                ('none', 'None', 'undefined'),  # null
            )
        ):
            nok_data = dict(json_spec_field=value)
            assert is_something_error(TypeError, validate_data_spec, nok_data, JsonSpec), value

    def test_json_bool(self):
        class JsonBoolSpec:
            json_bool_spec_field = Checker([JSON_BOOL])

        ok_data = dict(json_bool_spec_field='true')
        assert validate_data_spec(ok_data, JsonBoolSpec)

        ok_data = dict(json_bool_spec_field='false')
        assert validate_data_spec(ok_data, JsonBoolSpec)

        nok_data = dict(json_bool_spec_field=True)
        assert is_something_error(TypeError, validate_data_spec, nok_data, JsonBoolSpec)

        nok_data = dict(json_bool_spec_field='False')
        assert is_something_error(TypeError, validate_data_spec, nok_data, JsonBoolSpec)

        nok_data = dict(json_bool_spec_field='FALSE')
        assert is_something_error(TypeError, validate_data_spec, nok_data, JsonBoolSpec)

    def test_op_all(self):
        class AllSpec:
            all_field = Checker([LENGTH, STR, AMOUNT], LENGTH=dict(min=3, max=5))

        ok_data = dict(all_field='1.234')
        assert validate_data_spec(ok_data, AllSpec)

        ok_data = dict(all_field='12345')
        assert validate_data_spec(ok_data, AllSpec)

        nok_data = dict(all_field='123456')
        assert is_something_error(ValueError, validate_data_spec, nok_data, AllSpec)

    def test_op_any(self):
        class AnySpec:
            any_field = Checker([INT, STR], optional=True, op=CheckerOP.ANY)

        ok_data = dict(any_field=1)
        assert validate_data_spec(ok_data, AnySpec)

        ok_data = dict(any_field='1')
        assert validate_data_spec(ok_data, AnySpec)

        ok_data = dict(any_unexist_field=1)
        assert validate_data_spec(ok_data, AnySpec)

        nok_data = dict(any_field=True)
        assert is_something_error(TypeError, validate_data_spec, nok_data, AnySpec)

    def test_email(self):
        class EmailSpec:
            email_field = Checker([EMAIL])

        ok_data = dict(email_field='foo@bar.com')
        assert validate_data_spec(ok_data, EmailSpec)

        ok_data = dict(email_field='foo.bar@test.org')
        assert validate_data_spec(ok_data, EmailSpec)

        ok_data = dict(email_field='foo+bar@hc.co.uk')
        assert validate_data_spec(ok_data, EmailSpec)

        ok_data = dict(email_field='ABC@DEF.COM')
        assert validate_data_spec(ok_data, EmailSpec)

        ok_data = dict(email_field='_ab_C@example.com')
        assert validate_data_spec(ok_data, EmailSpec)

        ok_data = dict(email_field='-AB-c@example.com')
        assert validate_data_spec(ok_data, EmailSpec)

        ok_data = dict(email_field='3aBc@example.com')
        assert validate_data_spec(ok_data, EmailSpec)

        nok_data = dict(email_field="example.com")
        assert is_something_error(ValueError, validate_data_spec, nok_data, EmailSpec)

        nok_data = dict(email_field="john@doe.")
        assert is_something_error(ValueError, validate_data_spec, nok_data, EmailSpec)

        nok_data = dict(email_field="john@.doe")
        assert is_something_error(ValueError, validate_data_spec, nok_data, EmailSpec)

        nok_data = dict(email_field="say@hello.world!")
        assert is_something_error(ValueError, validate_data_spec, nok_data, EmailSpec)

    def test_regex_validator(self):
        # ^, $
        class SimpleRegexSpec1:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'^The'))

        # Just test SINGLE ONE regex spec for convenience
        class NoExtraSimpleRegexSpec1:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'^The'))

        class SimpleRegexSpec2:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'of the world$'))

        class SimpleRegexSpec3:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'^abc$'))

        class SimpleRegexSpec4:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'notice'))

        ok_data = dict(re_field='The')
        assert validate_data_spec(ok_data, SimpleRegexSpec1)
        assert validate_data_spec(ok_data, NoExtraSimpleRegexSpec1)
        nok_data = dict(re_field='That cat is cute')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec1)
        assert is_something_error(ValueError, validate_data_spec, nok_data, NoExtraSimpleRegexSpec1)
        nok_data = dict(re_field='I am the king of dogs')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec1)
        assert is_something_error(ValueError, validate_data_spec, nok_data, NoExtraSimpleRegexSpec1)

        ok_data = dict(re_field='of the world')
        assert validate_data_spec(ok_data, SimpleRegexSpec2)
        nok_data = dict(re_field='I am the king of the world.')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec2)

        ok_data = dict(re_field='abc')
        assert validate_data_spec(ok_data, SimpleRegexSpec3)
        nok_data = dict(re_field='adcd')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec3)
        nok_data = dict(re_field='adc')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec3)

        ok_data = dict(re_field='Did you notice that')
        assert validate_data_spec(ok_data, SimpleRegexSpec4)
        nok_data = dict(re_field='coffee, not iced please')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec4)

        # ?, +, *,
        class SimpleRegexSpec5:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'ab*'))

        class SimpleRegexSpec6:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'ab+'))

        class SimpleRegexSpec7:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'ab?'))

        class SimpleRegexSpec8:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'a?b+$'))

        ok_data = dict(re_field='ac')
        assert validate_data_spec(ok_data, SimpleRegexSpec5)
        ok_data = dict(re_field='ab')
        assert validate_data_spec(ok_data, SimpleRegexSpec5)
        ok_data = dict(re_field='abbc')
        assert validate_data_spec(ok_data, SimpleRegexSpec5)
        nok_data = dict(re_field='b')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec5)

        ok_data = dict(re_field='ab')
        assert validate_data_spec(ok_data, SimpleRegexSpec6)
        ok_data = dict(re_field='abbc')
        assert validate_data_spec(ok_data, SimpleRegexSpec6)
        nok_data = dict(re_field='ac')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec6)

        ok_data = dict(re_field='ac')
        assert validate_data_spec(ok_data, SimpleRegexSpec7)
        ok_data = dict(re_field='ab')
        assert validate_data_spec(ok_data, SimpleRegexSpec7)
        ok_data = dict(re_field='abbc')
        assert validate_data_spec(ok_data, SimpleRegexSpec7)
        nok_data = dict(re_field='bc')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec7)

        ok_data = dict(re_field='ab')
        assert validate_data_spec(ok_data, SimpleRegexSpec8)
        ok_data = dict(re_field='abb')
        assert validate_data_spec(ok_data, SimpleRegexSpec8)
        ok_data = dict(re_field='b')
        assert validate_data_spec(ok_data, SimpleRegexSpec8)
        ok_data = dict(re_field='bb')
        assert validate_data_spec(ok_data, SimpleRegexSpec8)
        nok_data = dict(re_field='aac')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec8)
        nok_data = dict(re_field='ba')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec8)

        # {}
        class SimpleRegexSpec9:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'ab{2}'))

        class SimpleRegexSpec10:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'ab{3,5}'))

        ok_data = dict(re_field='abb')
        assert validate_data_spec(ok_data, SimpleRegexSpec9)
        ok_data = dict(re_field='abcabbc')
        assert validate_data_spec(ok_data, SimpleRegexSpec9)
        nok_data = dict(re_field='ab')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec9)

        ok_data = dict(re_field='abbb')
        assert validate_data_spec(ok_data, SimpleRegexSpec10)
        ok_data = dict(re_field='abbabbbb')
        assert validate_data_spec(ok_data, SimpleRegexSpec10)
        nok_data = dict(re_field='abbabb')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec10)

        # |, ()
        class SimpleRegexSpec11:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'hello|world'))

        class SimpleRegexSpec12:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'(a|bc)de'))

        class SimpleRegexSpec13:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'(a|b)*c'))

        ok_data = dict(re_field='hello, hi')
        assert validate_data_spec(ok_data, SimpleRegexSpec11)
        ok_data = dict(re_field='new world')
        assert validate_data_spec(ok_data, SimpleRegexSpec11)
        nok_data = dict(re_field='hell, word')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec11)

        ok_data = dict(re_field='ade')
        assert validate_data_spec(ok_data, SimpleRegexSpec12)
        ok_data = dict(re_field='bcde')
        assert validate_data_spec(ok_data, SimpleRegexSpec12)
        nok_data = dict(re_field='adbce')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec12)

        ok_data = dict(re_field='c')
        assert validate_data_spec(ok_data, SimpleRegexSpec13)
        ok_data = dict(re_field='acb')
        assert validate_data_spec(ok_data, SimpleRegexSpec13)
        ok_data = dict(re_field='ebcd')
        assert validate_data_spec(ok_data, SimpleRegexSpec13)
        nok_data = dict(re_field='ab')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec13)

        # ., []
        class SimpleRegexSpec14:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'a.[0-9]'))

        class SimpleRegexSpec15:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'^.{3}$'))

        class SimpleRegexSpec16:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'[a-c]'))

        class SimpleRegexSpec17:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'[0-9]%'))

        class SimpleRegexSpec18:
            re_field = Checker([REGEX], REGEX=dict(pattern=r',[a-zA-Z0-9]$'))

        ok_data = dict(re_field='a33')
        assert validate_data_spec(ok_data, SimpleRegexSpec14)
        ok_data = dict(re_field='a.0')
        assert validate_data_spec(ok_data, SimpleRegexSpec14)
        ok_data = dict(re_field='a@9')
        assert validate_data_spec(ok_data, SimpleRegexSpec14)
        nok_data = dict(re_field='a8')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec14)
        nok_data = dict(re_field='a.a')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec14)

        ok_data = dict(re_field=',3c')
        assert validate_data_spec(ok_data, SimpleRegexSpec15)
        nok_data = dict(re_field='12')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec15)
        nok_data = dict(re_field='abcd')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec15)

        ok_data = dict(re_field='12a3c')
        assert validate_data_spec(ok_data, SimpleRegexSpec16)
        ok_data = dict(re_field='ab')
        assert validate_data_spec(ok_data, SimpleRegexSpec16)
        nok_data = dict(re_field='de')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec16)

        ok_data = dict(re_field='18%')
        assert validate_data_spec(ok_data, SimpleRegexSpec17)
        nok_data = dict(re_field='a%')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec17)

        ok_data = dict(re_field=',1')
        assert validate_data_spec(ok_data, SimpleRegexSpec18)
        ok_data = dict(re_field=',G')
        assert validate_data_spec(ok_data, SimpleRegexSpec18)
        nok_data = dict(re_field=',end')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SimpleRegexSpec18)

    def test_regex_match_method_validator(self):
        class SearchRegexSpec:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'watch out'))

        class MatchRegexSpec:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'watch out', method='match'))

        class FullmatchRegexSpec:
            re_field = Checker([REGEX], REGEX=dict(pattern=r'watch out', method='fullmatch'))

        ok_data = dict(re_field='someone tell me to watch out.')
        assert validate_data_spec(ok_data, SearchRegexSpec)
        nok_data = dict(re_field='someone tell me')
        assert is_something_error(ValueError, validate_data_spec, nok_data, SearchRegexSpec)

        ok_data = dict(re_field='watch out, it is close!')
        assert validate_data_spec(ok_data, MatchRegexSpec)
        nok_data = dict(re_field='someone tell me to watch out.')
        assert is_something_error(ValueError, validate_data_spec, nok_data, MatchRegexSpec)

        ok_data = dict(re_field='watch out')
        assert validate_data_spec(ok_data, FullmatchRegexSpec)
        nok_data = dict(re_field='watch out, it is close!')
        assert is_something_error(ValueError, validate_data_spec, nok_data, FullmatchRegexSpec)

    def test_uuid(self):
        class UuidSpec:
            uuid_field = Checker([UUID])

        uuid_inst = uuid.UUID('00000000-0000-0000-0000-000000000000')
        ok_data = dict(uuid_field=uuid_inst)
        assert validate_data_spec(ok_data, UuidSpec)

        ok_data = dict(uuid_field='92d88ec0-a1f2-439a-b3c0-9e36db8b0b75')
        assert validate_data_spec(ok_data, UuidSpec)

        ok_data = dict(uuid_field='{4700bb68-09b5-4c4f-a403-773c12ee166e}')
        assert validate_data_spec(ok_data, UuidSpec)

        ok_data = dict(uuid_field='urn:uuid:a4be2b64-caf3-4a00-a924-7ea848471e6c')
        assert validate_data_spec(ok_data, UuidSpec)

        nok_data = dict(uuid_field='z78ff51b-a354-4819-b2dd-bfaede3a8be5')
        assert is_something_error(ValueError, validate_data_spec, nok_data, UuidSpec)

    def test_not_checker(self):
        class NonBoolSpec:
            key = Checker([not_(BOOL)])

        class ListOfNonBoolSpec:
            keys = Checker([LIST_OF], LIST_OF=not_(BOOL))

        ok_data = dict(key=1)
        assert validate_data_spec(ok_data, NonBoolSpec)

        ok_data = dict(key='1')
        assert validate_data_spec(ok_data, NonBoolSpec)

        nok_data = dict(key=True)
        assert is_something_error(TypeError, validate_data_spec, nok_data, NonBoolSpec)

        ok_data = dict(keys=['1', 2, date(2000, 1, 1)])
        assert validate_data_spec(ok_data, ListOfNonBoolSpec)

        nok_data = dict(keys=['1', True, date(2000, 1, 1)])
        assert is_something_error(TypeError, validate_data_spec, nok_data, ListOfNonBoolSpec)

    def test_strict_mode(self):
        @dsv_feature(strict=True)
        class _LeafStrictSpec:
            d = Checker([BOOL])

        class _LeafNonStrictSpec:
            e = Checker([BOOL])

        class _MiddleSpec:
            c = Checker([BOOL])
            leaf_strict = Checker([LIST_OF], LIST_OF=SPEC, SPEC=_LeafStrictSpec)
            leaf_non_strict = Checker([SPEC], SPEC=_LeafNonStrictSpec)

        @dsv_feature(strict=True)
        class _RootStrictSpec:
            a = Checker([BOOL])
            middle = Checker([SPEC], SPEC=_MiddleSpec)

        ok_data = dict(
            a=True,
            middle=dict(
                c=False,
                leaf_strict=[dict(d=True), dict(d=False)],
                leaf_non_strict=dict(e=True, f=False),
                g=True,
            ),
        )
        assert validate_data_spec(ok_data, _RootStrictSpec)

        nok_data_root = dict(
            a=True,
            middle=dict(
                c=False,
                leaf_strict=[dict(d=True), dict(d=False)],
                leaf_non_strict=dict(e=True, f=False),
                g=True,
            ),
            unexpected_field=False,
        )
        assert is_something_error(ValueError, validate_data_spec, nok_data_root, _RootStrictSpec)

        nok_data_leaf = dict(
            a=True,
            middle=dict(
                c=False,
                leaf_strict=[dict(d=True), dict(d=False, unexpected_field=False)],
                leaf_non_strict=dict(e=True, f=False),
                g=True,
            ),
        )
        assert is_something_error(ValueError, validate_data_spec, nok_data_leaf, _RootStrictSpec)

    def test_any_keys_set(self):
        @dsv_feature(any_keys_set={('a', 'b')})
        class _AnyKeysSetEmptyFieldsSpec:
            pass

        assert validate_data_spec(dict(a=1, b=1), _AnyKeysSetEmptyFieldsSpec)
        assert validate_data_spec(dict(a=1), _AnyKeysSetEmptyFieldsSpec)
        assert validate_data_spec(dict(b=1), _AnyKeysSetEmptyFieldsSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(c=1), _AnyKeysSetEmptyFieldsSpec)

        @dsv_feature(any_keys_set={('a', 'b')})
        class _AnyKeysSetSpec:
            a = Checker([INT], optional=True)
            b = Checker([INT], optional=True)

        assert validate_data_spec(dict(a=1, b=1), _AnyKeysSetSpec)
        assert validate_data_spec(dict(a=1), _AnyKeysSetSpec)
        assert validate_data_spec(dict(b=1), _AnyKeysSetSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(c=1), _AnyKeysSetSpec)

        @dsv_feature(any_keys_set={('a', 'b'), ('c', 'd')})
        class _AnyKeysSetSpec:
            a = Checker([INT], optional=True)
            b = Checker([INT], optional=True)
            c = Checker([INT], optional=True)
            d = Checker([INT], optional=True)

        assert validate_data_spec(dict(a=1, c=1, d=1), _AnyKeysSetSpec)
        assert validate_data_spec(dict(a=1, c=1), _AnyKeysSetSpec)
        assert validate_data_spec(dict(a=1, d=1), _AnyKeysSetSpec)
        assert validate_data_spec(dict(b=1, c=1, d=1), _AnyKeysSetSpec)
        assert validate_data_spec(dict(b=1, c=1), _AnyKeysSetSpec)
        assert validate_data_spec(dict(b=1, d=1), _AnyKeysSetSpec)
        assert validate_data_spec(dict(a=1, b=1, c=1), _AnyKeysSetSpec)
        assert validate_data_spec(dict(a=1, b=1, d=1), _AnyKeysSetSpec)
        assert validate_data_spec(dict(a=1, b=1, c=1, d=1), _AnyKeysSetSpec)

        assert is_something_error(LookupError, validate_data_spec, dict(a=1), _AnyKeysSetSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(b=1), _AnyKeysSetSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(c=1), _AnyKeysSetSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(d=1), _AnyKeysSetSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(e=1), _AnyKeysSetSpec)

    def test_err_mode(self):
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

        with self.assertRaises(DSVError) as context:
            validate_data_spec(nok_data, _ErrModeAllSpec)
        assert len(context.exception.args) == 3

        def _get_nested_err_mode_spec(mode):
            @dsv_feature()
            class LeafSpec:
                int_f = Checker([INT])
                str_f = Checker([STR])
                bool_f = Checker([BOOL])

            class MidLeafSpec:
                int_f = Checker([INT])
                str_f = Checker([STR])
                leaf_f = Checker([SPEC], SPEC=LeafSpec)

            @dsv_feature(err_mode=mode)
            class RootSpec:
                int_f = Checker([INT])
                ml_f = Checker([SPEC], SPEC=MidLeafSpec)
                bool_f = Checker([BOOL])

            return RootSpec

        nok_data2 = dict(
            int_f='a',
            ml_f=dict(
                int_f=3.3,
                str_f='ok',
                leaf_f=dict(
                    int_f=1,
                    str_f=True,
                    bool_f='non-bool',
                ),
            ),
            bool_f='22',
        )

        with self.assertRaises(DSVError) as context:
            validate_data_spec(nok_data2, _get_nested_err_mode_spec(ErrorMode.ALL))
        assert len(context.exception.args) == 5

        with self.assertRaises(TypeError) as context:
            validate_data_spec(nok_data2, _get_nested_err_mode_spec(ErrorMode.MSE))
        assert len(context.exception.args) == 1

    def test_conditional_existence(self):
        """
        The existence cases of a, b, c. 2 * 2 * 2 = 8 cases.
        dict(a=1, b=1, c=1)
        dict(a=1, b=1)
        dict(a=1, c=1)
        dict(b=1, c=1)
        dict(a=1)
        dict(b=1)
        dict(c=1)
        dict(d=1)
        """
        # ==========================

        class _CondExistAOBOCOSpec:
            a = Checker([COND_EXIST], optional=True, COND_EXIST=dict(WITHOUT=['c']))
            b = Checker([COND_EXIST], optional=True, COND_EXIST=dict(WITH=['a'], WITHOUT=['c']))
            c = Checker([COND_EXIST], optional=True, COND_EXIST=dict(WITHOUT=['a']))

        assert validate_data_spec(dict(a=1, b=1), _CondExistAOBOCOSpec)
        assert validate_data_spec(dict(a=1), _CondExistAOBOCOSpec)
        assert validate_data_spec(dict(c=1), _CondExistAOBOCOSpec)
        assert validate_data_spec(dict(d=1), _CondExistAOBOCOSpec)

        assert is_something_error(KeyError, validate_data_spec, dict(a=1, b=1, c=1), _CondExistAOBOCOSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(a=1, c=1), _CondExistAOBOCOSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(b=1, c=1), _CondExistAOBOCOSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(b=1), _CondExistAOBOCOSpec)
        # ==========================

        class _CondExistABOCOSpec:
            a = Checker([COND_EXIST], COND_EXIST=dict(WITHOUT=['c']))
            b = Checker([COND_EXIST], optional=True, COND_EXIST=dict(WITH=['a'], WITHOUT=['c']))
            c = Checker([COND_EXIST], optional=True, COND_EXIST=dict(WITHOUT=['a']))

        assert validate_data_spec(dict(a=1, b=1), _CondExistABOCOSpec)
        assert validate_data_spec(dict(a=1), _CondExistABOCOSpec)

        assert is_something_error(KeyError, validate_data_spec, dict(a=1, b=1, c=1), _CondExistABOCOSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(a=1, c=1), _CondExistABOCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(b=1, c=1), _CondExistABOCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(b=1), _CondExistABOCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(c=1), _CondExistABOCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(d=1), _CondExistABOCOSpec)
        # ==========================

        class _CondExistAOBCOSpec:
            a = Checker([COND_EXIST], optional=True, COND_EXIST=dict(WITHOUT=['c']))
            b = Checker([COND_EXIST], COND_EXIST=dict(WITH=['a'], WITHOUT=['c']))
            c = Checker([COND_EXIST], optional=True, COND_EXIST=dict(WITHOUT=['a']))

        assert validate_data_spec(dict(a=1, b=1), _CondExistAOBCOSpec)

        assert is_something_error(KeyError, validate_data_spec, dict(a=1, b=1, c=1), _CondExistAOBCOSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(a=1, c=1), _CondExistAOBCOSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(b=1, c=1), _CondExistAOBCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1), _CondExistAOBCOSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(b=1), _CondExistAOBCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(c=1), _CondExistAOBCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(d=1), _CondExistAOBCOSpec)
        # ==========================

        class _CondExistAOBOCSpec:
            a = Checker([COND_EXIST], optional=True, COND_EXIST=dict(WITHOUT=['c']))
            b = Checker([COND_EXIST], optional=True, COND_EXIST=dict(WITH=['a'], WITHOUT=['c']))
            c = Checker([COND_EXIST], COND_EXIST=dict(WITHOUT=['a']))

        assert validate_data_spec(dict(c=1), _CondExistAOBOCSpec)

        assert is_something_error(KeyError, validate_data_spec, dict(a=1, b=1, c=1), _CondExistAOBOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1, b=1), _CondExistAOBOCSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(a=1, c=1), _CondExistAOBOCSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(b=1, c=1), _CondExistAOBOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1), _CondExistAOBOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(b=1), _CondExistAOBOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(d=1), _CondExistAOBOCSpec)
        # ==========================

        class _CondExistABCOSpec:
            a = Checker([COND_EXIST], COND_EXIST=dict(WITHOUT=['c']))
            b = Checker([COND_EXIST], COND_EXIST=dict(WITH=['a'], WITHOUT=['c']))
            c = Checker([COND_EXIST], optional=True, COND_EXIST=dict(WITHOUT=['a']))

        assert validate_data_spec(dict(a=1, b=1), _CondExistABCOSpec)

        assert is_something_error(KeyError, validate_data_spec, dict(a=1, b=1, c=1), _CondExistABCOSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(a=1, c=1), _CondExistABCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(b=1, c=1), _CondExistABCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1), _CondExistABCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(b=1), _CondExistABCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(c=1), _CondExistABCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(d=1), _CondExistABCOSpec)
        # ==========================

        class _CondExistABOCSpec:
            a = Checker([COND_EXIST], COND_EXIST=dict(WITHOUT=['c']))
            b = Checker([COND_EXIST], optional=True, COND_EXIST=dict(WITH=['a'], WITHOUT=['c']))
            c = Checker([COND_EXIST], COND_EXIST=dict(WITHOUT=['a']))

        assert is_something_error(KeyError, validate_data_spec, dict(a=1, b=1, c=1), _CondExistABOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1, b=1), _CondExistABOCSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(a=1, c=1), _CondExistABOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(b=1, c=1), _CondExistABOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1), _CondExistABOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(b=1), _CondExistABOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(c=1), _CondExistABOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(d=1), _CondExistABOCSpec)
        # ==========================

        class _CondExistAOBCSpec:
            a = Checker([COND_EXIST], optional=True, COND_EXIST=dict(WITHOUT=['c']))
            b = Checker([COND_EXIST], COND_EXIST=dict(WITH=['a'], WITHOUT=['c']))
            c = Checker([COND_EXIST], COND_EXIST=dict(WITHOUT=['a']))

        assert is_something_error(KeyError, validate_data_spec, dict(a=1, b=1, c=1), _CondExistAOBCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1, b=1), _CondExistAOBCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1, c=1), _CondExistAOBCSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(b=1, c=1), _CondExistAOBCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1), _CondExistAOBCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(b=1), _CondExistAOBCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(c=1), _CondExistAOBCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(d=1), _CondExistAOBCSpec)
        # ==========================

        class _CondExistABCSpec:
            a = Checker([COND_EXIST], COND_EXIST=dict(WITHOUT=['c']))
            b = Checker([COND_EXIST], COND_EXIST=dict(WITH=['a'], WITHOUT=['c']))
            c = Checker([COND_EXIST], COND_EXIST=dict(WITHOUT=['a']))

        assert is_something_error(KeyError, validate_data_spec, dict(a=1, b=1, c=1), _CondExistABCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1, b=1), _CondExistABCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1, c=1), _CondExistABCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(b=1, c=1), _CondExistABCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1), _CondExistABCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(b=1), _CondExistABCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(c=1), _CondExistABCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(d=1), _CondExistABCSpec)

    def test_optional_conditional_existence_other_check_fail(self):
        """
        The existence cases of a, b, c. 2 * 2 * 2 = 8 cases.
        dict(a=1, b=1, c=1)
        dict(a=1, b=1)
        dict(a=1, c=1)
        dict(b=1, c=1)
        dict(a=1)
        dict(b=1)
        dict(c=1)
        dict(d=1)
        """
        # ==========================
        class _CondExistOtherFailAOBOCOSpec:
            a = Checker([STR, COND_EXIST], optional=True, COND_EXIST=dict(WITHOUT=['c']))
            b = Checker([STR, COND_EXIST], optional=True, COND_EXIST=dict(WITH=['a'], WITHOUT=['c']))
            c = Checker([STR, COND_EXIST], optional=True, COND_EXIST=dict(WITHOUT=['a']))

        assert validate_data_spec(dict(d=1), _CondExistOtherFailAOBOCOSpec)
        # Spec Wise
        assert is_something_error(KeyError, validate_data_spec, dict(a=1, b=1, c=1), _CondExistOtherFailAOBOCOSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(a=1, c=1), _CondExistOtherFailAOBOCOSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(b=1, c=1), _CondExistOtherFailAOBOCOSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(b=1), _CondExistOtherFailAOBOCOSpec)
        # Field Wise
        assert is_something_error(TypeError, validate_data_spec, dict(a=1, b=1), _CondExistOtherFailAOBOCOSpec)
        assert is_something_error(TypeError, validate_data_spec, dict(a=1), _CondExistOtherFailAOBOCOSpec)
        assert is_something_error(TypeError, validate_data_spec, dict(c=1), _CondExistOtherFailAOBOCOSpec)

        # ==========================
        class _CondExistOtherFailABOCOSpec:
            a = Checker([STR, COND_EXIST], COND_EXIST=dict(WITHOUT=['c']))
            b = Checker([STR, COND_EXIST], optional=True, COND_EXIST=dict(WITH=['a'], WITHOUT=['c']))
            c = Checker([STR, COND_EXIST], optional=True, COND_EXIST=dict(WITHOUT=['a']))

        # SPec Wise
        assert is_something_error(KeyError, validate_data_spec, dict(a=1, b=1, c=1), _CondExistOtherFailABOCOSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(a=1, c=1), _CondExistOtherFailABOCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(b=1, c=1), _CondExistOtherFailABOCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(b=1), _CondExistOtherFailABOCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(c=1), _CondExistOtherFailABOCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(d=1), _CondExistOtherFailABOCOSpec)
        # Field Wise
        assert is_something_error(TypeError, validate_data_spec, dict(a=1, b=1), _CondExistOtherFailABOCOSpec)
        assert is_something_error(TypeError, validate_data_spec, dict(a=1), _CondExistOtherFailABOCOSpec)

        # ==========================
        class _CondExistOtherFailAOBCOSpec:
            a = Checker([STR, COND_EXIST], optional=True, COND_EXIST=dict(WITHOUT=['c']))
            b = Checker([STR, COND_EXIST], COND_EXIST=dict(WITH=['a'], WITHOUT=['c']))
            c = Checker([STR, COND_EXIST], optional=True, COND_EXIST=dict(WITHOUT=['a']))

        # SPec Wise
        assert is_something_error(KeyError, validate_data_spec, dict(a=1, b=1, c=1), _CondExistOtherFailAOBCOSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(a=1, c=1), _CondExistOtherFailAOBCOSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(b=1, c=1), _CondExistOtherFailAOBCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1), _CondExistOtherFailAOBCOSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(b=1), _CondExistOtherFailAOBCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(c=1), _CondExistOtherFailAOBCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(d=1), _CondExistOtherFailAOBCOSpec)
        # Field Wise
        assert is_something_error(TypeError, validate_data_spec, dict(a=1, b=1), _CondExistOtherFailAOBCOSpec)

        # ==========================
        class _CondExistOtherFailAOBOCSpec:
            a = Checker([STR, COND_EXIST], optional=True, COND_EXIST=dict(WITHOUT=['c']))
            b = Checker([STR, COND_EXIST], optional=True, COND_EXIST=dict(WITH=['a'], WITHOUT=['c']))
            c = Checker([STR, COND_EXIST], COND_EXIST=dict(WITHOUT=['a']))

        # Spec Wise
        assert is_something_error(KeyError, validate_data_spec, dict(a=1, b=1, c=1), _CondExistOtherFailAOBOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1, b=1), _CondExistOtherFailAOBOCSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(a=1, c=1), _CondExistOtherFailAOBOCSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(b=1, c=1), _CondExistOtherFailAOBOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1), _CondExistOtherFailAOBOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(b=1), _CondExistOtherFailAOBOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(d=1), _CondExistOtherFailAOBOCSpec)
        # Field Wise
        assert is_something_error(TypeError, validate_data_spec, dict(c=1), _CondExistOtherFailAOBOCSpec)
        # ==========================

        class _CondExistOtherFailABCOSpec:
            a = Checker([STR, COND_EXIST], COND_EXIST=dict(WITHOUT=['c']))
            b = Checker([STR, COND_EXIST], COND_EXIST=dict(WITH=['a'], WITHOUT=['c']))
            c = Checker([STR, COND_EXIST], optional=True, COND_EXIST=dict(WITHOUT=['a']))

        # Spec Wise
        assert is_something_error(KeyError, validate_data_spec, dict(a=1, b=1, c=1), _CondExistOtherFailABCOSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(a=1, c=1), _CondExistOtherFailABCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(b=1, c=1), _CondExistOtherFailABCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1), _CondExistOtherFailABCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(b=1), _CondExistOtherFailABCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(c=1), _CondExistOtherFailABCOSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(d=1), _CondExistOtherFailABCOSpec)
        # Field Wise
        assert is_something_error(TypeError, validate_data_spec, dict(a=1, b=1), _CondExistOtherFailABCOSpec)

        # ==========================
        class _CondExistOtherFailABOCSpec:
            a = Checker([STR, COND_EXIST], COND_EXIST=dict(WITHOUT=['c']))
            b = Checker([STR, COND_EXIST], optional=True, COND_EXIST=dict(WITH=['a'], WITHOUT=['c']))
            c = Checker([STR, COND_EXIST], COND_EXIST=dict(WITHOUT=['a']))

        # Spec Wise
        assert is_something_error(KeyError, validate_data_spec, dict(a=1, b=1, c=1), _CondExistOtherFailABOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1, b=1), _CondExistOtherFailABOCSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(a=1, c=1), _CondExistOtherFailABOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(b=1, c=1), _CondExistOtherFailABOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1), _CondExistOtherFailABOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(b=1), _CondExistOtherFailABOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(c=1), _CondExistOtherFailABOCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(d=1), _CondExistOtherFailABOCSpec)
        # ==========================

        class _CondExistOtherFailAOBCSpec:
            a = Checker([STR, COND_EXIST], optional=True, COND_EXIST=dict(WITHOUT=['c']))
            b = Checker([STR, COND_EXIST], COND_EXIST=dict(WITH=['a'], WITHOUT=['c']))
            c = Checker([STR, COND_EXIST], COND_EXIST=dict(WITHOUT=['a']))

        assert is_something_error(KeyError, validate_data_spec, dict(a=1, b=1, c=1), _CondExistOtherFailAOBCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1, b=1), _CondExistOtherFailAOBCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1, c=1), _CondExistOtherFailAOBCSpec)
        assert is_something_error(KeyError, validate_data_spec, dict(b=1, c=1), _CondExistOtherFailAOBCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(a=1), _CondExistOtherFailAOBCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(b=1), _CondExistOtherFailAOBCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(c=1), _CondExistOtherFailAOBCSpec)
        assert is_something_error(LookupError, validate_data_spec, dict(d=1), _CondExistOtherFailAOBCSpec)
        # ==========================


class TestCustomSpec(unittest.TestCase):
    def test_incorrect_validator_class(self):
        some_check = 'some_check'

        class InvalidClassValidator:
            name = some_check

            @staticmethod
            def validate(value, extra, data):
                return True, ValueError(f'{value} is not expected')

        from data_spec_validator.spec import custom_spec

        assert is_something_error(TypeError, custom_spec.register, dict(some_check=InvalidClassValidator()))

    def test_validator_been_overwritten(self):
        duplicate_check = 'd_check'

        class AValidator(BaseValidator):
            name = duplicate_check

            @staticmethod
            def validate(value, extra, data):
                return False, ValueError('a value error')

        class BValidator(BaseValidator):
            name = duplicate_check

            @staticmethod
            def validate(value, extra, data):
                return False, TypeError('a type error')

        from data_spec_validator.spec import custom_spec

        custom_spec.register(dict(duplicate_check=AValidator()))
        is_type_error(custom_spec.register, dict(duplicate_check=BValidator()))

    def test_custom_validator(self):
        gt_check = 'gt_check'

        class GreaterThanValidator(BaseValidator):
            name = gt_check

            @staticmethod
            def validate(value, extra, data):
                criteria = extra.get(GreaterThanValidator.name)
                return value > criteria, ValueError(f'{value} is not greater than {criteria}')

        from data_spec_validator.spec import custom_spec

        custom_spec.register(dict(gt_check=GreaterThanValidator()))

        class GreaterThanSpec:
            key = Checker([gt_check], GT_CHECK=10)

        ok_data = dict(key=11)
        assert validate_data_spec(ok_data, GreaterThanSpec)

        nok_data = dict(key=10)
        assert is_something_error(ValueError, validate_data_spec, nok_data, GreaterThanSpec)


class TestCheckKeyword(unittest.TestCase):
    def test_check_keyword_must_upper_case(self):
        assert Checker([STR], WHAT_EVER=True, MUST_BE_UPPER={'1': 1, '2': 2}, CASE=[1, 2])

        with self.assertRaises(TypeError):
            Checker([STR], WHAT_eVER=True)

    def test_blacklist_check_keyword(self):
        with self.assertRaises(TypeError):
            Checker([STR], ALLOW_NONE=True)

        with self.assertRaises(TypeError):
            Checker([STR], OP='SOME_OP')

        with self.assertRaises(TypeError):
            Checker([STR], OPTIONAL=True)

        with self.assertRaises(TypeError) as cm:
            Checker([ONE_OF], op=CheckerOP.ANY, OP='SOME_OP', ONE_OF=[1, 2], ALLOW_NONE=True)
        self.assertEqual('Forbidden keyword arguments: ALLOW_NONE, OP', str(cm.exception))


class TestMessageLevel(unittest.TestCase):
    def test_vague_message(self):
        def _get_int_spec():
            class IntSpec:
                int_field = Checker([INT])

            return IntSpec

        reset_msg_level(vague=True)
        nok_data = dict(int_field='3')
        try:
            validate_data_spec(nok_data, _get_int_spec())
        except Exception as e:
            assert str(e).find('well-formatted') >= 0

        reset_msg_level()
        try:
            validate_data_spec(nok_data, _get_int_spec())
        except Exception as e:
            assert str(e).find('reason') >= 0


class TestMultipleRowSpec(unittest.TestCase):
    def test_multirow_spec(self):
        def _get_singlerow_spec():
            class SingleRowSpec:
                i_field = Checker([INT])
                s_field = Checker([STR])

            return SingleRowSpec

        ok_data = [dict(i_field=1, s_field='1'), dict(i_field=2, s_field='2'), dict(i_field=3, s_field='3')]
        assert validate_data_spec(ok_data, _get_singlerow_spec(), multirow=True)

        nok_data = [dict(i_field=1, s_field=1), dict(i_field=2, s_field='2')]
        is_something_error(TypeError, validate_data_spec, nok_data, _get_singlerow_spec(), multirow=True)

        with self.assertRaises(ValueError) as ctx:
            nok_data = dict(i_field=1, s_field='1')
            validate_data_spec(nok_data, _get_singlerow_spec(), multirow=True)
        assert 'SingleRowSpec' in str(ctx.exception)


if __name__ == '__main__':
    unittest.main()
