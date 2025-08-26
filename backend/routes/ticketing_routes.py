from auth.dependencies import get_current_user_id, require_role
# File: backend/routes/ticketing_routes.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from services.ticketing_service import TicketingService, TicketingError

# Adjust this import to your project's auth dependency location
try:
    from auth.dependencies import require_role
except Exception:
    # Fallback no-op that allows all (remove in production)
    def require_role(roles):
        async def _noop():
            return True
        return _noop

router = APIRouter(prefix="/tickets", tags=["Ticketing"])

svc = TicketingService()
svc.ensure_schema()

class TicketTypeIn(BaseModel):
    
event_id: int
    name: str
    price_cents: int
    total_qty: int
    currency: str = "USD"
    max_per_user: int = 10
    sales_start: str | None = None
    sales_end: str | None = None
    is_active: bool = True

class TicketItemIn(BaseModel):
    
ticket_type_id: int
    qty: int

class PurchaseIn(BaseModel):
    
    event_id: int
    items: List[TicketItemIn]

@router.get("/status", dependencies=[Depends(require_role(["admin", "moderator", "band_member"]))])
async def check_ticketing_status():
    return {"status": "Ticketing system operational."}

@router.post("/types", dependencies=[Depends(require_role(["admin", "moderator"]))])
async def create_ticket_type(payload: TicketTypeIn):
    try:
        tid = svc.create_ticket_type(**payload.model_dump())
        return {"id": tid}
    except TicketingError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/types/{event_id}", dependencies=[Depends(require_role(["admin", "moderator", "band_member"]))])
async def list_ticket_types(event_id: int):
    return svc.list_ticket_types(event_id)

@router.post("/purchase", dependencies=[Depends(require_role(["band_member", "admin", "moderator"]))])
async def purchase_tickets(payload: PurchaseIn):
    try:
        oid = svc.purchase_tickets(
            user_id=payload.user_id,
            event_id=payload.event_id,
            items=[i.model_dump() for i in payload.items],
        )
        return {"order_id": oid}
    except TicketingError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/refund/{order_id}", dependencies=[Depends(require_role(["admin", "moderator"]))])
async def refund_order(order_id: int, reason: str = ""):
    try:
        return svc.refund_order(order_id, reason)
    except TicketingError as e:
        raise HTTPException(status_code=400, detail=str(e))
