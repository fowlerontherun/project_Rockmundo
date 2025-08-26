from auth.dependencies import get_current_user_id, require_role
# File: backend/routes/gifting_routes.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, conint
from typing import List, Optional

from services.gifting_service import GiftingService, GiftingError, DigitalGiftIn, TicketGiftIn, TicketGiftItem

# Auth dependency (replace with your real one)
try:
    from auth.dependencies import require_role
except Exception:
    def require_role(roles):
        async def _noop():
            return True
        return _noop

router = APIRouter(prefix="/gifts", tags=["Gifting"])
svc = GiftingService()
svc.ensure_schema()

# -------- payload models --------
class DigitalGiftPayload(BaseModel):
    
sender_user_id: int
    recipient_user_id: int
    work_type: str   # 'song' | 'album'
    work_id: int
    price_cents: conint(ge=0)
    currency: str = "USD"
    message: Optional[str] = None

class TicketGiftItemPayload(BaseModel):
    
ticket_type_id: int
    qty: conint(gt=0)

class TicketGiftPayload(BaseModel):
    
sender_user_id: int
    recipient_user_id: int
    event_id: int
    items: List[TicketGiftItemPayload]
    currency: str = "USD"
    message: Optional[str] = None

# -------- endpoints --------
@router.post("/digital", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def gift_digital(payload: DigitalGiftPayload):
    try:
        gift_id = svc.gift_digital(DigitalGiftIn(**payload.model_dump()))
        return {"gift_id": gift_id}
    except GiftingError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/tickets", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def gift_tickets(payload: TicketGiftPayload):
    try:
        items = [TicketGiftItem(**i.model_dump()) for i in payload.items]
        gift_id = svc.gift_tickets(TicketGiftIn(
            sender_user_id=payload.sender_user_id,
            recipient_user_id=payload.recipient_user_id,
            event_id=payload.event_id,
            items=items,
            currency=payload.currency,
            message=payload.message
        ))
        return {"gift_id": gift_id}
    except GiftingError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/inbox/{user_id}", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def gifts_inbox(user_id: int, limit: int = 50, offset: int = 0):
    return svc.list_inbox(user_id, limit, offset)

@router.get("/sent/{user_id}", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def gifts_sent(user_id: int, limit: int = 50, offset: int = 0):
    return svc.list_sent(user_id, limit, offset)
