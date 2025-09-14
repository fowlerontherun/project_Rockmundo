"""Convenience re-export for HTTP error handlers.

This module exposes the :func:`http_exception_handler` from
:mod:`backend.utils.error_handlers` so consumers can import it from
``utils``.
"""

from backend.utils.error_handlers import http_exception_handler

__all__ = ["http_exception_handler"]

