from typing import Union, Tuple, Set, Optional, Type, Callable


class _DSVFeatureParams:
    __slots__ = ('_strict', '_any_keys_set')

    def __init__(self, strict, any_keys_set: Union[Set[Tuple[str, ...]], None]):
        self._strict = strict
        self._any_keys_set = any_keys_set or set()

    @property
    def strict(self) -> bool:
        return self._strict

    @property
    def any_keys_set(self) -> set:
        return self._any_keys_set

    def __repr__(self):
        return f'_DSVFeatureParams(strict={self._strict}, any_keys_set={self._any_keys_set})'


_FEAT_PARAMS = '__feat_params__'


def _process_class(cls: Type, strict: bool, any_keys_set: Union[Set[Tuple[str, ...]], None]) -> Type:

    setattr(cls, _FEAT_PARAMS, _DSVFeatureParams(strict, any_keys_set))

    return cls


def dsv_feature(strict: bool = False, any_keys_set: Optional[Set[Tuple[str, ...]]] = None) -> Callable:

    def wrap(cls: Type) -> Type:
        return _process_class(cls, strict, any_keys_set)

    return wrap


def is_strict(spec) -> bool:
    feat_params: Union[_DSVFeatureParams, None] = getattr(spec, _FEAT_PARAMS, None)
    return bool(feat_params and feat_params.strict)


def get_any_keys_set(spec) -> Set[Tuple[str, ...]]:
    feat_params: Union[_DSVFeatureParams, None] = getattr(spec, _FEAT_PARAMS, None)
    return feat_params.any_keys_set if feat_params else set()

