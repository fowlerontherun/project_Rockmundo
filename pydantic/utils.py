"""Minimal subset of ``pydantic.utils`` required for FastAPI tests."""

def lenient_issubclass(cls, class_or_tuple):  # pragma: no cover - simple
    try:
        return issubclass(cls, class_or_tuple)
    except Exception:
        return False

__all__ = ["lenient_issubclass"]
