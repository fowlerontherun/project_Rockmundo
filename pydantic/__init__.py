"""Minimal subset of the :mod:`pydantic` API used in tests.

This lightweight implementation provides ``BaseModel``, ``BaseSettings`` and
``Field`` with very small feature sets so that the rest of the project can
define configuration models without requiring the real dependency.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, get_args, get_origin

# Minimal stand-ins for types expected by FastAPI
AnyUrl = str
BaseConfig = object

def field_validator(*_args, **_kwargs):  # pragma: no cover - simple no-op
    def decorator(func):
        return func

    return decorator

ConfigDict = dict


class ValidationError(Exception):
    pass


class FieldInfo:
    """Store metadata about a model field."""

    def __init__(
        self,
        default: Any = None,
        *,
        default_factory=None,
        env: str | None = None,
        **kwargs,
    ):
        self.default = default
        self.default_factory = default_factory
        self.env = env
        self.alias = kwargs.get("alias")
        self.convert_underscores = kwargs.get("convert_underscores")


def Field(default: Any = None, *, default_factory=None, env: str | None = None, **kwargs) -> FieldInfo:
    """Return a ``FieldInfo`` describing a model field.

    Only the ``default``, ``default_factory`` and ``env`` parameters are
    recognised; all other arguments are accepted for compatibility but ignored.
    """

    return FieldInfo(default, default_factory=default_factory, env=env)


class BaseModel:
    """Very small subset of :class:`pydantic.BaseModel`."""

    def __init__(self, **data: Any) -> None:
        annotations = getattr(self.__class__, "__annotations__", {})
        for name, annotation in annotations.items():
            field = getattr(self.__class__, name, None)
            if isinstance(field, FieldInfo):
                value = field.default_factory() if field.default_factory is not None else field.default
                env_name = field.env
            else:
                value = field
                env_name = None
            if env_name:
                env_val = os.getenv(env_name)
                if env_val is not None:
                    value = self._coerce(env_val, annotation)
            setattr(self, name, value)

        for key, value in data.items():
            setattr(self, key, value)

    def dict(self) -> dict[str, Any]:  # pragma: no cover - trivial
        return self.__dict__.copy()

    @classmethod
    def update_forward_refs(cls, **kwargs):  # pragma: no cover - placeholder
        return None

    @staticmethod
    def _coerce(value: str, field_type: Any) -> Any:
        """Convert environment string values to the declared type."""

        origin = get_origin(field_type)
        if field_type == int:
            return int(value)
        if field_type == float:
            return float(value)
        if field_type == bool:
            return value.lower() in {"1", "true", "yes", "on"}
        if origin == list and get_args(field_type) == (str,):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value


class BaseSettings(BaseModel):
    """Minimal ``BaseSettings`` reading values from environment variables."""

    class Config:
        env_file = None  # type: ignore[assignment]

    def __init__(self, **data: Any) -> None:
        cfg = getattr(self.__class__, "Config", None)
        env_file = getattr(cfg, "env_file", None)
        if env_file:
            path = Path(env_file)
            if path.exists():
                for line in path.read_text().splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

        super().__init__(**data)


def create_model(name: str, **fields: Any) -> type:
    """Dynamically create a ``BaseModel`` subclass.

    This minimal stand-in only supports declaring field annotations and default
    values. It is sufficient for FastAPI's usage in the tests.
    """

    annotations: dict[str, Any] = {}
    attrs: dict[str, Any] = {}
    for field_name, value in fields.items():
        if isinstance(value, tuple):
            annotations[field_name] = value[0]
            attrs[field_name] = value[1]
        else:
            annotations[field_name] = value
    attrs["__annotations__"] = annotations
    return type(name, (BaseModel,), attrs)
