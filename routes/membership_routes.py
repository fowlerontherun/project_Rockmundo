from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user_id, require_permission
from services.economy_service import EconomyError, EconomyService
from services.membership_service import membership_service

router = APIRouter(prefix="/membership", tags=["Membership"])

_economy = EconomyService()
_economy.ensure_schema()


async def _current_user(user_id: int = Depends(get_current_user_id)) -> int:
    await require_permission(["user", "band_member", "moderator", "admin"], user_id)
    return user_id


class JoinIn(BaseModel):
    tier: str


@router.get("/tiers")
def list_tiers():
    return membership_service.list_tiers()


@router.get("/me")
def get_my_membership(user_id: int = Depends(_current_user)):
    return membership_service.get_membership(user_id) or {}


@router.post("/join")
def join_membership(payload: JoinIn, user_id: int = Depends(_current_user)):
    try:
        fee = membership_service.join(user_id, payload.tier)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    try:
        if fee:
            _economy.transfer(user_id, 0, fee)
    except EconomyError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    membership = membership_service.get_membership(user_id)
    return {"status": "ok", "renew_at": membership["renew_at"], "fee_cents": fee}


@router.post("/renew")
def renew_membership(user_id: int = Depends(_current_user)):
    try:
        fee = membership_service.renew(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    try:
        if fee:
            _economy.transfer(user_id, 0, fee)
    except EconomyError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    membership = membership_service.get_membership(user_id)
    return {"status": "ok", "renew_at": membership["renew_at"], "fee_cents": fee}


@router.post("/cancel")
def cancel_membership(user_id: int = Depends(_current_user)):
    membership_service.cancel(user_id)
    return {"status": "ok"}
