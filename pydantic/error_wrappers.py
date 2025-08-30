"""Stub implementations for FastAPI's limited use of pydantic.error_wrappers."""

from __future__ import annotations


class ErrorWrapper(Exception):  # pragma: no cover
    pass


class ValidationError(Exception):  # pragma: no cover
    def __init__(self, errors):
        self._errors = errors

    def errors(self):  # pragma: no cover
        return self._errors
