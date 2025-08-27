"""Admin endpoints for moderating user submitted media."""

from fastapi import APIRouter, Request
from auth.dependencies import get_current_user_id, require_role
from services.admin_service import AdminService


router = APIRouter(prefix="/media", tags=["Admin Media Moderation"])


class _AdminDB:
    def insert_admin_action(self, action):  # pragma: no cover - placeholder behaviour
        pass


admin_logger = AdminService(_AdminDB())


@router.post("/flag/{media_id}")
async def flag_media(media_id: int, req: Request):
    """Flag a piece of media for review."""
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    admin_logger.log_action(admin_id, "media_flag", {"media_id": media_id})
    return {"status": "flagged", "media_id": media_id}


@router.post("/approve/{media_id}")
async def approve_media(media_id: int, req: Request):
    """Approve a media item."""
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    admin_logger.log_action(admin_id, "media_approve", {"media_id": media_id})
    return {"status": "approved", "media_id": media_id}

