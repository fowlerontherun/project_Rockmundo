"""Deprecated module for NPC band routes.

The old Flask blueprint has been removed in favour of the FastAPI
implementation in :mod:`backend.routes.admin_npc_routes` and the
``NPCService`` class. This file remains only to avoid import errors.
"""

from warnings import warn

warn(
    "backend.routes.npc_band_routes is deprecated; use admin_npc_routes instead",
    DeprecationWarning,
)
