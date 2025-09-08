"""Mail API routes.

Endpoints for sending, listing, and deleting mail messages.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth.dependencies import get_current_user_id
from services.mailbox_service import delete_message, get_inbox, send_message


router = APIRouter(prefix="/mail", tags=["Mail"])


class MailSendIn(BaseModel):
    """Payload for sending a new mail message."""

    recipient_id: int
    subject: str
    body: str


@router.post("/")
async def send_mail(payload: MailSendIn, user_id: int = Depends(get_current_user_id)):
    """Send a mail message from the authenticated user."""
    return await send_message(user_id, payload.recipient_id, payload.subject, payload.body)


@router.get("/")
async def list_mail(user_id: int = Depends(get_current_user_id)):
    """Return the inbox for the authenticated user."""
    return await get_inbox(user_id)


@router.delete("/{message_id}")
async def delete_mail(message_id: int, user_id: int = Depends(get_current_user_id)):
    """Delete a mail message owned by the authenticated user."""
    return await delete_message(message_id, user_id)

