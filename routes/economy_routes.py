"""FastAPI routes for the economy service."""

from typing import List

from fastapi import APIRouter, HTTPException, Depends
from auth.character_dependencies import get_current_character_id
from pydantic import BaseModel
from services.economy_service import (
    EconomyError,
    EconomyService,
    TransactionRecord,
)

router = APIRouter(prefix="/economy", tags=["Economy"])

svc = EconomyService()
svc.ensure_schema()


class AccountCreateIn(BaseModel):
    user_id: int
    currency: str = "USD"


class AmountIn(BaseModel):
    amount_cents: int
    currency: str = "USD"


class TransferIn(BaseModel):
    from_user_id: int
    to_user_id: int
    amount_cents: int
    currency: str = "USD"


@router.post("/accounts")
def create_account(payload: AccountCreateIn, character_id: int = Depends(get_current_character_id)):
    if payload.user_id != character_id:
        raise HTTPException(status_code=403, detail="Wallet belongs to the selected character")
    try:
        svc.deposit(character_id, 0, currency=payload.currency)
        return {"user_id": character_id}
    except EconomyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/accounts/{user_id}")
def get_balance(user_id: int, character_id: int = Depends(get_current_character_id)):
    if user_id != character_id:
        raise HTTPException(status_code=403, detail="Wallet belongs to the selected character")
    return {"user_id": character_id, "balance_cents": svc.get_balance(character_id)}


@router.post("/accounts/{user_id}/deposit")
def deposit(user_id: int, payload: AmountIn, character_id: int = Depends(get_current_character_id)):
    if user_id != character_id:
        raise HTTPException(status_code=403, detail="Wallet belongs to the selected character")
    try:
        svc.deposit(character_id, payload.amount_cents, currency=payload.currency)
        return {"balance_cents": svc.get_balance(character_id)}
    except EconomyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/accounts/{user_id}/withdraw")
def withdraw(user_id: int, payload: AmountIn, character_id: int = Depends(get_current_character_id)):
    if user_id != character_id:
        raise HTTPException(status_code=403, detail="Wallet belongs to the selected character")
    try:
        svc.withdraw(character_id, payload.amount_cents, currency=payload.currency)
        return {"balance_cents": svc.get_balance(user_id)}
    except EconomyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/transfer")
def transfer(payload: TransferIn, character_id: int = Depends(get_current_character_id)):
    if payload.from_user_id != character_id:
        raise HTTPException(status_code=403, detail="Transfers must originate from the selected character")
    try:
        svc.transfer(character_id, payload.to_user_id, payload.amount_cents, currency=payload.currency)
        return {"ok": True}
    except EconomyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/accounts/{user_id}/transactions", response_model=List[TransactionRecord])
def list_transactions(user_id: int, limit: int = 50, character_id: int = Depends(get_current_character_id)):
    if user_id != character_id:
        raise HTTPException(status_code=403, detail="Wallet belongs to the selected character")
    return svc.list_transactions(character_id, limit=limit)
