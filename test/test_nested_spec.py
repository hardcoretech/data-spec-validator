import unittest

from data_spec_validator.spec import BOOL, DICT, DIGIT_STR, FLOAT, INT, NONE, SPEC, STR, Checker, validate_data_spec

from .utils import is_something_error


class TestNestedSpec(unittest.TestCase):
    def test_nested(self):
        class NestedSpec:
            class ChildSpec1:
                class ChildSpec11:
                    f_11 = Checker([FLOAT])
                    d_11 = Checker([DICT])
                    b_11 = Checker([BOOL])

                f_1 = Checker([FLOAT])
                d_1 = Checker([DICT])
                b_1 = Checker([BOOL])
                s_1 = Checker([SPEC], SPEC=ChildSpec11)

            class ChildSpec2:
                s_2 = Checker([STR])

            class ChildSpec3:
                n_3 = Checker([NONE])
                ds_3 = Checker([DIGIT_STR])

            c1_f = Checker([SPEC], SPEC=ChildSpec1)
            int_f = Checker([INT])
            str_f = Checker([STR])
            c2_f = Checker([SPEC], SPEC=ChildSpec2)
            c3_f = Checker([SPEC], SPEC=ChildSpec3)

        ok_data = dict(
            c1_f=dict(
                f_1=3.4,
                d_1=dict(a=1),
                b_1=True,
                s_1=dict(
                    f_11=1.1,
                    d_11=dict(b=[]),
                    b_11=False,
                ),
            ),
            int_f=9,
            str_f='first str',
            c2_f=dict(s_2='second str'),
            c3_f=dict(
                n_3=None,
                ds_3='99',
            ),
        )
        assert validate_data_spec(ok_data, NestedSpec)

        nok_data = dict(
            c1_f=3,
            int_f='9',
            str_f=3,
            c2_f=None,
            c3_f=[],
        )
        assert is_something_error(TypeError, validate_data_spec, nok_data, NestedSpec)
