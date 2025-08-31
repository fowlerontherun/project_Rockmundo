from __future__ import annotations

from . import FieldInfo  # Re-export

SHAPE_FROZENSET = 0
SHAPE_LIST = 1
SHAPE_SEQUENCE = 2
SHAPE_SET = 3
SHAPE_SINGLETON = 4
SHAPE_TUPLE = 5
SHAPE_TUPLE_ELLIPSIS = 6


class ModelField:  # pragma: no cover - simple placeholder
    pass


class UndefinedType:  # pragma: no cover
    pass


Undefined = UndefinedType()
