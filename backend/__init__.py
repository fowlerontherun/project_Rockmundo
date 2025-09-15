"""Compatibility helpers for legacy ``backend`` imports.

This package exposes the project's top-level modules (like ``models`` and
``services``) under the ``backend`` namespace so that existing import paths
such as ``backend.models`` continue to work.
"""

from pathlib import Path

_backend_dir = Path(__file__).resolve().parent
_project_root = _backend_dir.parent

# Search the actual ``backend`` package directory first so that modules that
# live there (e.g. ``backend.utils``) are resolved correctly.  The project
# root is also included to allow imports like ``backend.models``.
__path__ = [
    str(_backend_dir),
    str(_project_root),
]
