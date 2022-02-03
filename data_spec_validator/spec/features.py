from typing import Union


class _DSVFeatureParams:
    __slots__ = ('_strict',)

    def __init__(self, strict):
        self._strict = strict

    @property
    def strict(self) -> bool:
        return self._strict

    def __repr__(self):
        return f'_DSVFeatureParams(strict={self._strict})'


_FEAT_PARAMS = '__feat_params__'


def _process_class(cls, strict) -> type:

    setattr(cls, _FEAT_PARAMS, _DSVFeatureParams(strict))

    return cls


def dsv_feature(strict=False) -> type:
    def wrap(cls):
        return _process_class(cls, strict)

    return wrap


def is_strict(spec) -> bool:
    feat_params: Union[_DSVFeatureParams, None] = getattr(spec, _FEAT_PARAMS, None)
    return bool(feat_params and feat_params.strict)
