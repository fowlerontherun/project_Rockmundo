from fastapi import APIRouter, Depends, File, Form, UploadFile
from auth.dependencies import get_current_user_id, require_permission
from services.mailbox_service import delete_message, get_inbox, send_message
from services.storage_service import save_attachment

router = APIRouter()


@router.post("/mail/send", dependencies=[Depends(require_permission(["admin", "moderator"]))])
async def send_message_route(
    recipient_id: int = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    files: list[UploadFile] = File([]),
    user_id: int = Depends(get_current_user_id),
):
    """Send a mail message on behalf of an admin or moderator."""
    attachments = [await save_attachment(f) for f in files]
    return await send_message(user_id, recipient_id, subject, body, attachments)


@router.get("/mail/inbox")
async def inbox(user_id: int = Depends(get_current_user_id)):
    """Return the inbox for the authenticated user."""
    return await get_inbox(user_id)


@router.delete("/mail/{message_id}")
async def archive(message_id: int, user_id: int = Depends(get_current_user_id)):
    """Archive (soft delete) a mail message."""
    return await delete_message(message_id, user_id)
