"""Expose the FastAPI application instance.

This tiny module allows tools like ``uvicorn`` to load the pre-configured
application by importing :mod:`backend.api`.
"""

from .main import app

__all__ = ["app"]
