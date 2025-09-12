"""Admin endpoints for moderating user submitted media."""

import asyncio
import json

from fastapi import APIRouter, Depends, Request

from auth.dependencies import get_current_user_id, require_permission
from services.admin_audit_service import audit_dependency
from services.admin_service import AdminActionRepository, AdminService
from services.storage_service import get_storage_backend
from services.skin_service import SkinService

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
skin_service = SkinService()


@router.post("/flag/{media_id}")
async def flag_media(media_id: int, req: Request):
    """Flag a piece of media for review."""
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
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
    await require_permission(["admin"], admin_id)
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


@router.get("/queue")
async def list_submission_queue(req: Request):
    """List pending skin submissions awaiting moderation."""

    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    queue = skin_service.list_submission_queue()
    return [s.__dict__ for s in queue]


@router.post("/review/{submission_id}/{decision}")
async def review_submission(submission_id: int, decision: str, req: Request):
    """Approve or reject a skin submission."""

    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    approved = decision.lower() == "approve"
    review = skin_service.review_submission(submission_id, admin_id, approved)
    return {"review_id": review.id, "status": review.decision}
