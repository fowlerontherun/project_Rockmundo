"""Minimal stubs for ``pydantic.class_validators``.

These placeholders satisfy imports from FastAPI in the test environment.
The full validation behaviour of Pydantic is not required for the tests,
so the constructs simply act as no-op stand-ins.
"""

from __future__ import annotations

from typing import Any, Iterable


class ModelField:  # pragma: no cover - simple container
    def __init__(self, name: str, type_: Any) -> None:
        self.name = name
        self.type_ = type_


class Validator:  # pragma: no cover - simple callable wrapper
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class ValidatorGroup(list):  # pragma: no cover
    pass


FieldsSet = set[str]


def make_generic_validator(*args, **kwargs):  # pragma: no cover
    def _validator(value):
        return value

    return _validator


def rebuild_model_schema(*args, **kwargs):  # pragma: no cover
    return None
