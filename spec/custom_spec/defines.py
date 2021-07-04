"""
Add CUSTOM validator to your project.

`CUSTOM` here refers to those validators which involves your business code logic or design,
i.g. accessing DB field, accessing ORM model method, calculate employee's salary...etc


How to add a custom validator, for example
    1) Define a name for customized validator in custom_spec/defines.py

        BY_PASS = 'by_pass'

    2) Implement the validator in custom_spec/validators.py

        class ByPassValidator(metaclass=BaseValidator):
            def validate(value, extra, data):
                return True, 'nothing can be wrong'

    3) Update map inside |def get_custom_check_2_validator_map|, e.g.

        def get_custom_check_2_validator_map():
            from .validators import ByPassValidator
            return {
               BY_PASS: ByPassValidator(),
            }

    4) Export the name 'BY_PASS' in custom_spec/__init__.py so that this name of check can be
       imported by calling `from spec import BY_PASS`
"""

# DB related (Permission/Runtime), be aware of performance
EXIST = 'exist'


def get_custom_check_2_validator_map():
    from .validators import ExistValidator

    return {
        EXIST: ExistValidator(),
    }
