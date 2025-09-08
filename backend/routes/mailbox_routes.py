from fastapi import APIRouter, Depends
from auth.dependencies import get_current_user_id, require_permission
from services.mailbox_service import delete_message, get_inbox, send_message

router = APIRouter()


@router.post("/mail/send", dependencies=[Depends(require_permission(["admin", "moderator"]))])
async def send_message_route(payload: dict, user_id: int = Depends(get_current_user_id)):
    """Send a mail message on behalf of an admin or moderator."""
    return await send_message(
        user_id, payload["recipient_id"], payload["subject"], payload["body"]
    )


@router.get("/mail/inbox")
async def inbox(user_id: int = Depends(get_current_user_id)):
    """Return the inbox for the authenticated user."""
    return await get_inbox(user_id)


@router.delete("/mail/{message_id}")
async def archive(message_id: int, user_id: int = Depends(get_current_user_id)):
    """Archive (soft delete) a mail message."""
    return await delete_message(message_id, user_id)
