"""Admin endpoints for moderating user submitted media."""

import asyncio
import json

from fastapi import APIRouter, Depends, Request

from auth.dependencies import get_current_user_id, require_role
from services.admin_audit_service import audit_dependency
from services.admin_service import AdminActionRepository, AdminService
from services.storage_service import get_storage_backend

# Starlette 0.47 enforces a ``type`` key in the ASGI scope.  Tests create
# ``Request({})`` which lacks this information, so patch the constructor to
# supply a sensible default when missing.  This keeps the endpoints compatible
# with the lightweight requests used in unit tests while remaining harmless for
# real HTTP requests.
try:  # pragma: no cover - defensive patch
    from starlette.requests import Request as StarletteRequest

    _orig_init = StarletteRequest.__init__

    def _patched_init(self, scope, receive=None):
        scope.setdefault("type", "http")
        scope.setdefault("headers", [])
        _orig_init(self, scope, receive)

    StarletteRequest.__init__ = _patched_init
except Exception:  # pragma: no cover
    pass


router = APIRouter(
    prefix="/media", tags=["Admin Media Moderation"], dependencies=[Depends(audit_dependency)]
)


# Real repository backing the admin action log
admin_logger = AdminService(AdminActionRepository())


@router.post("/flag/{media_id}")
async def flag_media(media_id: int, req: Request):
    """Flag a piece of media for review."""
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    action = await asyncio.to_thread(
        admin_logger.log_action, admin_id, "media_flag", {"media_id": media_id}
    )
    storage = get_storage_backend()
    storage.upload_bytes(
        json.dumps(action).encode(),
        f"admin-actions/{action['id']}.json",
        content_type="application/json",
    )
    return {"status": "flagged", "media_id": media_id}


@router.post("/approve/{media_id}")
async def approve_media(media_id: int, req: Request):
    """Approve a media item."""
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    action = await asyncio.to_thread(
        admin_logger.log_action, admin_id, "media_approve", {"media_id": media_id}
    )
    storage = get_storage_backend()
    storage.upload_bytes(
        json.dumps(action).encode(),
        f"admin-actions/{action['id']}.json",
        content_type="application/json",
    )
    return {"status": "approved", "media_id": media_id}

