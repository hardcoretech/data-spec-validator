import unittest
from datetime import date
from itertools import chain

from data_spec_validator.spec import (
    AMOUNT,
    AMOUNT_RANGE,
    ANY_KEY_EXISTS,
    BOOL,
    DATE,
    DATE_RANGE,
    DECIMAL_PLACE,
    DICT,
    EMAIL,
    INT,
    JSON,
    JSON_BOOL,
    KEY_COEXISTS,
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
    not_,
    validate_data_spec,
)
from data_spec_validator.spec.validators import BaseValidator


def is_something_error(error, func, *args):
    try:
        func(*args)
    except error:
        return True
    return False


def is_type_error(func, *args):
    try:
        func(*args)
    except TypeError:
        return True
    return False


class TestSpec(unittest.TestCase):
    def test_int(self):
        def _get_int_spec():
            class IntSpec:
                int_field = Checker([INT])

            return IntSpec

        ok_data = dict(int_field=3)
        assert validate_data_spec(ok_data, _get_int_spec())

        nok_data = dict(int_field='3')
        assert is_something_error(TypeError, validate_data_spec, nok_data, _get_int_spec())

    def test_str(self):
        def _get_str_spec():
            class StrSpec:
                str_field = Checker([STR])

            return StrSpec

        ok_data = dict(str_field='3')
        assert validate_data_spec(ok_data, _get_str_spec())

        nok_data = dict(str_field=3)
        assert is_something_error(TypeError, validate_data_spec, nok_data, _get_str_spec())

    def test_none(self):
        def _get_none_spec():
            class NoneSpec:
                none_field = Checker([NONE])

            return NoneSpec

        ok_data = dict(none_field=None)
        assert validate_data_spec(ok_data, _get_none_spec())

        nok_data = dict(none_field=3)
        assert is_something_error(TypeError, validate_data_spec, nok_data, _get_none_spec())

    def test_bool(self):
        def _get_bool_spec():
            class BoolSpec:
                bool_field = Checker([BOOL])

            return BoolSpec

        ok_data = dict(bool_field=False)
        assert validate_data_spec(ok_data, _get_bool_spec())

        nok_data = dict(bool_field='True')
        assert is_something_error(TypeError, validate_data_spec, nok_data, _get_bool_spec())

    def test_self(self):
        def _get_self_spec():
            class SelfSpec:
                next_field = Checker([SPEC], optional=True, extra={SPEC: SELF})
                children = Checker([LIST_OF], optional=True, extra={LIST_OF: SPEC, SPEC: SELF})

            return SelfSpec

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
        assert validate_data_spec(ok_data, _get_self_spec())

        nok_data = dict(next_field=dict(next_field=0))
        assert is_something_error(Exception, validate_data_spec, nok_data, _get_self_spec())

    def test_list(self):
        def _get_list_spec():
            class ListSpec:
                list_field = Checker([LIST])

            return ListSpec

        ok_data = dict(list_field=[1, 2, 3])
        assert validate_data_spec(ok_data, _get_list_spec())

        nok_data = dict(list_field=dict(a=2, b=4))
        assert is_something_error(TypeError, validate_data_spec, nok_data, _get_list_spec())

    def test_dict(self):
        def _get_dict_spec():
            class DictSpec:
                dict_field = Checker([DICT])

            return DictSpec

        ok_data = dict(dict_field=dict(a=2, b=4))
        assert validate_data_spec(ok_data, _get_dict_spec())

        nok_data = dict(dict_field=[1, 2, 3])
        assert is_something_error(TypeError, validate_data_spec, nok_data, _get_dict_spec())

    def test_optional(self):
        def _get_optional_spec():
            class OptionalSpec:
                optional_field = Checker([STR], optional=True)

            return OptionalSpec

        ok_data = dict(whatever_field='dont_care')
        assert validate_data_spec(ok_data, _get_optional_spec())

    def test_amount(self):
        def _get_amount_spec():
            class AmountSpec:
                amount_field = Checker([AMOUNT])

            return AmountSpec

        ok_data = dict(amount_field='3.1415')
        assert validate_data_spec(ok_data, _get_amount_spec())

        ok_data = dict(amount_field=5566)
        assert validate_data_spec(ok_data, _get_amount_spec())

        nok_data = dict(amount_field='abc')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_amount_spec())

    def test_amount_range(self):
        def _get_amount_range_spec():
            class AmountRangeSpec:
                amount_range_field = Checker([AMOUNT_RANGE], extra={AMOUNT_RANGE: dict(min=-2.1, max=3.8)})

            return AmountRangeSpec

        ok_data = dict(
            amount_range_field='3.8',
        )
        assert validate_data_spec(ok_data, _get_amount_range_spec())

        ok_data = dict(amount_range_field=-2.1)
        assert validate_data_spec(ok_data, _get_amount_range_spec())

        nok_data = dict(amount_range_field='-2.2')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_amount_range_spec())

        nok_data = dict(amount_range_field='3.81')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_amount_range_spec())

    def test_length(self):
        def _get_length_spec():
            class LengthSpec:
                length_field = Checker([LENGTH], extra={LENGTH: dict(min=3, max=5)})

            return LengthSpec

        ok_data = dict(length_field='3.2')
        assert validate_data_spec(ok_data, _get_length_spec())

        ok_data = dict(length_field='3.141')
        assert validate_data_spec(ok_data, _get_length_spec())

        nok_data = dict(length_field='ah')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_length_spec())

        nok_data = dict(length_field='exceed')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_length_spec())

    def test_decimal_place(self):
        def _get_decimal_place_spec():
            class DecimalPlaceSpec:
                decimal_place_field = Checker([DECIMAL_PLACE], extra={DECIMAL_PLACE: 4})

            return DecimalPlaceSpec

        ok_data = dict(decimal_place_field=3.123)
        assert validate_data_spec(ok_data, _get_decimal_place_spec())

        ok_data = dict(decimal_place_field=3.1234)
        assert validate_data_spec(ok_data, _get_decimal_place_spec())

        nok_data = dict(decimal_place_field=3.12345)
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_decimal_place_spec())

    def test_date(self):
        def _get_date_spec():
            class DateSpec:
                date_field = Checker([DATE])

            return DateSpec

        ok_data = dict(date_field='2000-01-31')
        assert validate_data_spec(ok_data, _get_date_spec())

        ok_data = dict(date_field='1-31-2000')
        assert validate_data_spec(ok_data, _get_date_spec())

        ok_data = dict(date_field='20200101')
        assert validate_data_spec(ok_data, _get_date_spec())

        nok_data = dict(date_field='202011')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_date_spec())

    def test_date_range(self):
        def _get_date_range_spec():
            class DateRangeSpec:
                date_range_field = Checker(
                    [DATE_RANGE],
                    extra={DATE_RANGE: dict(min='2000-01-01', max='2010-12-31')},
                )

            return DateRangeSpec

        ok_data = dict(date_range_field='2000-1-1')
        assert validate_data_spec(ok_data, _get_date_range_spec())

        ok_data = dict(date_range_field='2005-12-31')
        assert validate_data_spec(ok_data, _get_date_range_spec())

        ok_data = dict(date_range_field='2010-12-31')
        assert validate_data_spec(ok_data, _get_date_range_spec())

        nok_data = dict(date_range_field='1999-12-31')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_date_range_spec())

    def test_nested_spec(self):
        def _get_spec():
            class LeafSpec:
                int_field = Checker([INT])
                str_field = Checker([STR])
                bool_field = Checker([BOOL])

            class MidLeafSpec:
                int_field = Checker([INT])
                str_field = Checker([STR])
                leaf_field = Checker([SPEC], extra={SPEC: LeafSpec})

            class RootSpec:
                int_field = Checker([INT])
                mid_leaf_field = Checker([SPEC], extra={SPEC: MidLeafSpec})
                bool_field = Checker([BOOL])

            return RootSpec

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
        assert validate_data_spec(ok_data, _get_spec())

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
        assert is_something_error(TypeError, validate_data_spec, nok_data, _get_spec())

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
        assert is_something_error(TypeError, validate_data_spec, nok_data, _get_spec())

    def test_list_of(self):
        def _get_list_of_spec_spec():
            class ChildSpec:
                int_field = Checker([INT])
                bool_field = Checker([BOOL])

            class ParentSpec:
                list_of_spec_field = Checker([LIST_OF], extra={LIST_OF: SPEC, SPEC: ChildSpec})

            return ParentSpec

        ok_data = dict(
            list_of_spec_field=[
                dict(int_field=1, bool_field=False),
                dict(int_field=2, bool_field=True),
                dict(int_field=3, bool_field=False),
            ]
        )
        assert validate_data_spec(ok_data, _get_list_of_spec_spec())

        nok_data = dict(
            list_of_spec_field=[
                dict(int_field=1, bool_field=False),
                2,
            ]
        )
        assert is_something_error(TypeError, validate_data_spec, nok_data, _get_list_of_spec_spec())

        def _get_list_of_int_spec():
            class ListOfIntSpec:
                list_of_int_field = Checker([LIST_OF], extra={LIST_OF: INT})

            return ListOfIntSpec

        ok_data = dict(list_of_int_field=[1, 2, 3])
        assert validate_data_spec(ok_data, _get_list_of_int_spec())

        nok_data = dict(list_of_int_field=[1, 2, '3'])
        assert is_something_error(TypeError, validate_data_spec, nok_data, _get_list_of_int_spec())

    def test_one_of(self):
        def _get_one_of_spec():
            class OneOfSpec:
                one_of_spec_field = Checker([ONE_OF], extra={ONE_OF: [1, '2', [3, 4], {'5': 6}]})

            return OneOfSpec

        ok_data = dict(one_of_spec_field=1)
        assert validate_data_spec(ok_data, _get_one_of_spec())

        ok_data = dict(one_of_spec_field='2')
        assert validate_data_spec(ok_data, _get_one_of_spec())

        ok_data = dict(one_of_spec_field=[3, 4])
        assert validate_data_spec(ok_data, _get_one_of_spec())

        ok_data = dict(one_of_spec_field={'5': 6})
        assert validate_data_spec(ok_data, _get_one_of_spec())

        nok_data = dict(one_of_spec_field=6)
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_one_of_spec())

    def test_json(self):
        def _get_json_spec():
            class JsonSpec:
                json_spec_field = Checker([JSON])

            return JsonSpec

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
            assert validate_data_spec(ok_data, _get_json_spec()), value

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
            assert is_something_error(TypeError, validate_data_spec, nok_data, _get_json_spec()), value

    def test_json_bool(self):
        def _get_json_bool_spec():
            class JsonBoolSpec:
                json_bool_spec_field = Checker([JSON_BOOL])

            return JsonBoolSpec

        ok_data = dict(json_bool_spec_field='true')
        assert validate_data_spec(ok_data, _get_json_bool_spec())

        ok_data = dict(json_bool_spec_field='false')
        assert validate_data_spec(ok_data, _get_json_bool_spec())

        nok_data = dict(json_bool_spec_field=True)
        assert is_something_error(TypeError, validate_data_spec, nok_data, _get_json_bool_spec())

        nok_data = dict(json_bool_spec_field='False')
        assert is_something_error(TypeError, validate_data_spec, nok_data, _get_json_bool_spec())

        nok_data = dict(json_bool_spec_field='FALSE')
        assert is_something_error(TypeError, validate_data_spec, nok_data, _get_json_bool_spec())

    def test_op_all(self):
        def _get_all_spec():
            class AllSpec:
                all_field = Checker([LENGTH, STR, AMOUNT], extra={LENGTH: dict(min=3, max=5)})

            return AllSpec

        ok_data = dict(all_field='1.234')
        assert validate_data_spec(ok_data, _get_all_spec())

        ok_data = dict(all_field='12345')
        assert validate_data_spec(ok_data, _get_all_spec())

        nok_data = dict(all_field='123456')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_all_spec())

    def test_op_any(self):
        def _get_any_spec():
            class AnySpec:
                any_field = Checker([INT, STR], optional=True, op=CheckerOP.ANY)

            return AnySpec

        ok_data = dict(any_field=1)
        assert validate_data_spec(ok_data, _get_any_spec())

        ok_data = dict(any_field='1')
        assert validate_data_spec(ok_data, _get_any_spec())

        ok_data = dict(any_unexist_field=1)
        assert validate_data_spec(ok_data, _get_any_spec())

        nok_data = dict(any_field=True)
        assert is_something_error(TypeError, validate_data_spec, nok_data, _get_any_spec())

    def test_email(self):
        def _get_email_spec():
            class EmailSpec:
                email_field = Checker([EMAIL])

            return EmailSpec

        ok_data = dict(email_field='foo@bar.com')
        assert validate_data_spec(ok_data, _get_email_spec())

        ok_data = dict(email_field='foo.bar@test.org')
        assert validate_data_spec(ok_data, _get_email_spec())

        ok_data = dict(email_field='foo+bar@hc.co.uk')
        assert validate_data_spec(ok_data, _get_email_spec())

        nok_data = dict(email_field="example.com")
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_email_spec())

        nok_data = dict(email_field="john@doe.")
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_email_spec())

        nok_data = dict(email_field="john@.doe")
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_email_spec())

        nok_data = dict(email_field="say@hello.world!")
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_email_spec())

    def test_regex_validator(self):
        # ^, $
        def _get_symbol_spec1():
            class SimpleRegexSpec1:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'^The')})

            return SimpleRegexSpec1

        def _get_symbol_spec2():
            class SimpleRegexSpec2:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'of the world$')})

            return SimpleRegexSpec2

        def _get_symbol_spec3():
            class SimpleRegexSpec3:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'^abc$')})

            return SimpleRegexSpec3

        def _get_symbol_spec4():
            class SimpleRegexSpec4:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'notice')})

            return SimpleRegexSpec4

        ok_data = dict(re_field='The')
        assert validate_data_spec(ok_data, _get_symbol_spec1())
        nok_data = dict(re_field='That cat is cute')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec1())
        nok_data = dict(re_field='I am the king of dogs')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec1())

        ok_data = dict(re_field='of the world')
        assert validate_data_spec(ok_data, _get_symbol_spec2())
        nok_data = dict(re_field='I am the king of the world.')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec2())

        ok_data = dict(re_field='abc')
        assert validate_data_spec(ok_data, _get_symbol_spec3())
        nok_data = dict(re_field='adcd')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec3())
        nok_data = dict(re_field='adc')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec3())

        ok_data = dict(re_field='Did you notice that')
        assert validate_data_spec(ok_data, _get_symbol_spec4())
        nok_data = dict(re_field='coffee, not iced please')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec4())

        # ?, +, *,
        def _get_symbol_spec5():
            class SimpleRegexSpec5:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'ab*')})

            return SimpleRegexSpec5

        def _get_symbol_spec6():
            class SimpleRegexSpec6:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'ab+')})

            return SimpleRegexSpec6

        def _get_symbol_spec7():
            class SimpleRegexSpec7:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'ab?')})

            return SimpleRegexSpec7

        def _get_symbol_spec8():
            class SimpleRegexSpec8:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'a?b+$')})

            return SimpleRegexSpec8

        ok_data = dict(re_field='ac')
        assert validate_data_spec(ok_data, _get_symbol_spec5())
        ok_data = dict(re_field='ab')
        assert validate_data_spec(ok_data, _get_symbol_spec5())
        ok_data = dict(re_field='abbc')
        assert validate_data_spec(ok_data, _get_symbol_spec5())
        nok_data = dict(re_field='b')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec5())

        ok_data = dict(re_field='ab')
        assert validate_data_spec(ok_data, _get_symbol_spec6())
        ok_data = dict(re_field='abbc')
        assert validate_data_spec(ok_data, _get_symbol_spec6())
        nok_data = dict(re_field='ac')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec6())

        ok_data = dict(re_field='ac')
        assert validate_data_spec(ok_data, _get_symbol_spec7())
        ok_data = dict(re_field='ab')
        assert validate_data_spec(ok_data, _get_symbol_spec7())
        ok_data = dict(re_field='abbc')
        assert validate_data_spec(ok_data, _get_symbol_spec7())
        nok_data = dict(re_field='bc')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec7())

        ok_data = dict(re_field='ab')
        assert validate_data_spec(ok_data, _get_symbol_spec8())
        ok_data = dict(re_field='abb')
        assert validate_data_spec(ok_data, _get_symbol_spec8())
        ok_data = dict(re_field='b')
        assert validate_data_spec(ok_data, _get_symbol_spec8())
        ok_data = dict(re_field='bb')
        assert validate_data_spec(ok_data, _get_symbol_spec8())
        nok_data = dict(re_field='aac')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec8())
        nok_data = dict(re_field='ba')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec8())

        # {}
        def _get_symbol_spec9():
            class SimpleRegexSpec9:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'ab{2}')})

            return SimpleRegexSpec9

        def _get_symbol_spec10():
            class SimpleRegexSpec10:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'ab{3,5}')})

            return SimpleRegexSpec10

        ok_data = dict(re_field='abb')
        assert validate_data_spec(ok_data, _get_symbol_spec9())
        ok_data = dict(re_field='abcabbc')
        assert validate_data_spec(ok_data, _get_symbol_spec9())
        nok_data = dict(re_field='ab')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec9())

        ok_data = dict(re_field='abbb')
        assert validate_data_spec(ok_data, _get_symbol_spec10())
        ok_data = dict(re_field='abbabbbb')
        assert validate_data_spec(ok_data, _get_symbol_spec10())
        nok_data = dict(re_field='abbabb')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec10())

        # |, ()
        def _get_symbol_spec11():
            class SimpleRegexSpec11:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'hello|world')})

            return SimpleRegexSpec11

        def _get_symbol_spec12():
            class SimpleRegexSpec12:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'(a|bc)de')})

            return SimpleRegexSpec12

        def _get_symbol_spec13():
            class SimpleRegexSpec13:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'(a|b)*c')})

            return SimpleRegexSpec13

        ok_data = dict(re_field='hello, hi')
        assert validate_data_spec(ok_data, _get_symbol_spec11())
        ok_data = dict(re_field='new world')
        assert validate_data_spec(ok_data, _get_symbol_spec11())
        nok_data = dict(re_field='hell, word')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec11())

        ok_data = dict(re_field='ade')
        assert validate_data_spec(ok_data, _get_symbol_spec12())
        ok_data = dict(re_field='bcde')
        assert validate_data_spec(ok_data, _get_symbol_spec12())
        nok_data = dict(re_field='adbce')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec12())

        ok_data = dict(re_field='c')
        assert validate_data_spec(ok_data, _get_symbol_spec13())
        ok_data = dict(re_field='acb')
        assert validate_data_spec(ok_data, _get_symbol_spec13())
        ok_data = dict(re_field='ebcd')
        assert validate_data_spec(ok_data, _get_symbol_spec13())
        nok_data = dict(re_field='ab')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec13())

        # ., []
        def _get_symbol_spec14():
            class SimpleRegexSpec14:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'a.[0-9]')})

            return SimpleRegexSpec14

        def _get_symbol_spec15():
            class SimpleRegexSpec15:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'^.{3}$')})

            return SimpleRegexSpec15

        def _get_symbol_spec16():
            class SimpleRegexSpec16:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'[a-c]')})

            return SimpleRegexSpec16

        def _get_symbol_spec17():
            class SimpleRegexSpec17:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'[0-9]%')})

            return SimpleRegexSpec17

        def _get_symbol_spec18():
            class SimpleRegexSpec18:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r',[a-zA-Z0-9]$')})

            return SimpleRegexSpec18

        ok_data = dict(re_field='a33')
        assert validate_data_spec(ok_data, _get_symbol_spec14())
        ok_data = dict(re_field='a.0')
        assert validate_data_spec(ok_data, _get_symbol_spec14())
        ok_data = dict(re_field='a@9')
        assert validate_data_spec(ok_data, _get_symbol_spec14())
        nok_data = dict(re_field='a8')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec14())
        nok_data = dict(re_field='a.a')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec14())

        ok_data = dict(re_field=',3c')
        assert validate_data_spec(ok_data, _get_symbol_spec15())
        nok_data = dict(re_field='12')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec15())
        nok_data = dict(re_field='abcd')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec15())

        ok_data = dict(re_field='12a3c')
        assert validate_data_spec(ok_data, _get_symbol_spec16())
        ok_data = dict(re_field='ab')
        assert validate_data_spec(ok_data, _get_symbol_spec16())
        nok_data = dict(re_field='de')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec16())

        ok_data = dict(re_field='18%')
        assert validate_data_spec(ok_data, _get_symbol_spec17())
        nok_data = dict(re_field='a%')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec17())

        ok_data = dict(re_field=',1')
        assert validate_data_spec(ok_data, _get_symbol_spec18())
        ok_data = dict(re_field=',G')
        assert validate_data_spec(ok_data, _get_symbol_spec18())
        nok_data = dict(re_field=',end')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_symbol_spec18())

    def test_regex_match_method_validator(self):
        def _get_search_spec():
            class SearchRegexSpec:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'watch out')})

            return SearchRegexSpec

        def _get_match_spec():
            class MatchRegexSpec:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'watch out', method='match')})

            return MatchRegexSpec

        def _get_fullmatch_spec():
            class FullmatchRegexSpec:
                re_field = Checker([REGEX], extra={REGEX: dict(pattern=r'watch out', method='fullmatch')})

            return FullmatchRegexSpec

        ok_data = dict(re_field='someone tell me to watch out.')
        assert validate_data_spec(ok_data, _get_search_spec())
        nok_data = dict(re_field='someone tell me')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_search_spec())

        ok_data = dict(re_field='watch out, it is close!')
        assert validate_data_spec(ok_data, _get_match_spec())
        nok_data = dict(re_field='someone tell me to watch out.')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_match_spec())

        ok_data = dict(re_field='watch out')
        assert validate_data_spec(ok_data, _get_fullmatch_spec())
        nok_data = dict(re_field='watch out, it is close!')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_fullmatch_spec())

    def test_uuid(self):
        def _get_uuid_spec():
            class UuidSpec:
                uuid_field = Checker([UUID])

            return UuidSpec

        ok_data = dict(uuid_field='92d88ec0-a1f2-439a-b3c0-9e36db8b0b75')
        assert validate_data_spec(ok_data, _get_uuid_spec())

        ok_data = dict(uuid_field='{4700bb68-09b5-4c4f-a403-773c12ee166e}')
        assert validate_data_spec(ok_data, _get_uuid_spec())

        ok_data = dict(uuid_field='urn:uuid:a4be2b64-caf3-4a00-a924-7ea848471e6c')
        assert validate_data_spec(ok_data, _get_uuid_spec())

        nok_data = dict(uuid_field='z78ff51b-a354-4819-b2dd-bfaede3a8be5')
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_uuid_spec())

    def test_any_key_exists(self):
        def _get_any_key_exists_spec():
            class AnyKeyExistsSpec:
                test_checker = Checker([ANY_KEY_EXISTS], extra={ANY_KEY_EXISTS: {'key1', 'key2', 'key3'}})

            return AnyKeyExistsSpec

        ok_data = dict(key1=1)
        assert validate_data_spec(ok_data, _get_any_key_exists_spec())

        ok_data = dict(key2=1, key3=1)
        assert validate_data_spec(ok_data, _get_any_key_exists_spec())

        nok_data = dict(key=1)
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_any_key_exists_spec())

    def test_key_coexist(self):
        def _get_key_coexist_spec():
            class KeyCoexistsSpec:
                key1 = Checker([KEY_COEXISTS], extra={KEY_COEXISTS: ['key2']})

            return KeyCoexistsSpec

        ok_data = dict(key1=1, key2=1)
        assert validate_data_spec(ok_data, _get_key_coexist_spec())

        nok_data = dict(key2=1)
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_key_coexist_spec())

        nok_data = dict(key=1)
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_key_coexist_spec())

    def test_not_checker(self):
        def _get_non_bool_spec():
            class NonBoolSpec:
                key = Checker([not_(BOOL)])

            return NonBoolSpec

        def _get_list_of_non_bool_spec():
            class ListOfNonBoolSpec:
                keys = Checker([LIST_OF], extra={LIST_OF: not_(BOOL)})

            return ListOfNonBoolSpec

        ok_data = dict(key=1)
        assert validate_data_spec(ok_data, _get_non_bool_spec())

        ok_data = dict(key='1')
        assert validate_data_spec(ok_data, _get_non_bool_spec())

        nok_data = dict(key=True)
        assert is_something_error(TypeError, validate_data_spec, nok_data, _get_non_bool_spec())

        ok_data = dict(keys=['1', 2, date(2000, 1, 1)])
        assert validate_data_spec(ok_data, _get_list_of_non_bool_spec())

        nok_data = dict(keys=['1', True, date(2000, 1, 1)])
        assert is_something_error(TypeError, validate_data_spec, nok_data, _get_list_of_non_bool_spec())


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

        def _get_gt_10_spec():
            class GreaterThanSpec:
                key = Checker([gt_check], extra={gt_check: 10})

            return GreaterThanSpec

        ok_data = dict(key=11)
        assert validate_data_spec(ok_data, _get_gt_10_spec())

        nok_data = dict(key=10)
        assert is_something_error(ValueError, validate_data_spec, nok_data, _get_gt_10_spec())


if __name__ == '__main__':
    unittest.main()
