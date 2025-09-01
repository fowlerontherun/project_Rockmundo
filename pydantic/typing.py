"""Minimal subset of ``pydantic.typing`` used by FastAPI in tests."""

def evaluate_forwardref(type_, globalns, localns=None):  # pragma: no cover - trivial
    return type_

__all__ = ["evaluate_forwardref"]
