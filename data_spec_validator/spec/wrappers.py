from typing import Tuple

from .defines import BaseValidator, BaseWrapper


class NotWrapper(BaseWrapper, BaseValidator):
    name = 'not'

    def validate(self, value, extra, data) -> Tuple[bool, Exception]:
        ok, error = self.wrapped_func(value, extra, data)
        info = '' if not ok else TypeError(f'Value({value}) should not pass {self.wrapped_func.__str__()}')
        return not ok, info
