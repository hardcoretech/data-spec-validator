from typing import Callable, Optional, Set, Tuple, Type, Union

from .checks import Checker
from .defines import FOREACH, SPEC, ErrorMode


class _DSVFeatureParams:
    __slots__ = ('_strict', '_any_keys_set', '_err_mode')

    def __init__(self, strict, any_keys_set: Union[Set[Tuple[str, ...]], None], err_mode):
        self._strict = strict
        self._any_keys_set = any_keys_set or set()
        self._err_mode = err_mode

    @property
    def err_mode(self) -> ErrorMode:
        return self._err_mode

    @property
    def strict(self) -> bool:
        return self._strict

    @property
    def any_keys_set(self) -> set:
        return self._any_keys_set

    def __repr__(self):
        return f'_DSVFeatureParams(strict={self._strict}, any_keys_set={self._any_keys_set}, err_mode={self._err_mode})'


_FEAT_PARAMS = '__feat_params__'


def _process_class(
    cls: Type, strict: bool, any_keys_set: Union[Set[Tuple[str, ...]], None], err_mode: ErrorMode
) -> Type:

    setattr(cls, _FEAT_PARAMS, _DSVFeatureParams(strict, any_keys_set, err_mode))

    return cls


def dsv_feature(
    strict: bool = False, any_keys_set: Optional[Set[Tuple[str, ...]]] = None, err_mode=ErrorMode.MSE
) -> Callable:
    def wrap(cls: Type) -> Type:
        return _process_class(cls, strict, any_keys_set, err_mode)

    return wrap


def get_err_mode(spec) -> ErrorMode:
    feat_params: Union[_DSVFeatureParams, None] = getattr(spec, _FEAT_PARAMS, None)
    return feat_params.err_mode if feat_params else ErrorMode.MSE


def is_strict(spec) -> bool:
    feat_params: Union[_DSVFeatureParams, None] = getattr(spec, _FEAT_PARAMS, None)
    return bool(feat_params and feat_params.strict)


def get_any_keys_set(spec) -> Set[Tuple[str, ...]]:
    feat_params: Union[_DSVFeatureParams, None] = getattr(spec, _FEAT_PARAMS, None)
    return feat_params.any_keys_set if feat_params else set()


def repack_multirow(data, spec):
    class _InternalMultiSpec:
        dsv_multirow = Checker([FOREACH], FOREACH=SPEC, SPEC=spec)

    new_data = dict(dsv_multirow=data)
    return new_data, _InternalMultiSpec
