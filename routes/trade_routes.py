from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.dependencies import get_current_user_id, require_permission
from services.trade_route_service import TradeRouteService

router = APIRouter(prefix="/trade", tags=["Trade"])

trade_service = TradeRouteService()


async def _current_user(user_id: int = Depends(get_current_user_id)) -> int:
    await require_permission(["user", "band_member", "moderator", "admin"], user_id)
    return user_id


class TradeIn(BaseModel):
    source_city: str
    dest_city: str
    goods: str
    quantity: int = 1
    value_cents: int


@router.post("/routes")
def create_route(payload: TradeIn, user_id: int = Depends(_current_user)):
    return trade_service.schedule_trade(
        payload.source_city,
        payload.dest_city,
        payload.goods,
        payload.quantity,
        payload.value_cents,
    )


@router.get("/routes/{route_id}")
def route_detail(route_id: int, user_id: int = Depends(_current_user)):
    route = trade_service.get_route(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route


@router.get("/routes")
def route_list(user_id: int = Depends(_current_user)):
    return trade_service.list_routes()
