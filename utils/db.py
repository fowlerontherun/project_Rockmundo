"""Convenience re-exports for database helpers.

This module exposes the synchronous and asynchronous connection
helpers from :mod:`backend.utils.db`.  The synchronous ``get_conn``
wrapper uses the underlying asynchronous driver but remains available
for legacy callers.  New code should prefer :func:`aget_conn`.  Additional
utilities such as :func:`cached_query`, :func:`init_pool`, and
:func:`_init_pool_async` are also re-exported for convenience.
"""

from backend.utils.db import (
    _init_pool_async,
    aget_conn,
    cached_query,
    get_conn,
    init_pool,
)

__all__ = [
    "get_conn",
    "aget_conn",
    "cached_query",
    "init_pool",
    "_init_pool_async",
]
