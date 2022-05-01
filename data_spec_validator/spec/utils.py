from typing import Union


def raise_if(condition: bool, error: Union[TypeError, RuntimeError, ValueError, NotImplementedError]):
    if condition:
        raise error
