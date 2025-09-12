"""FastAPI routes for the economy service."""

from typing import List

from fastapi import APIRouter, HTTPException
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
def create_account(payload: AccountCreateIn):
    try:
        svc.deposit(payload.user_id, 0, currency=payload.currency)
        return {"user_id": payload.user_id}
    except EconomyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/accounts/{user_id}")
def get_balance(user_id: int):
    return {"user_id": user_id, "balance_cents": svc.get_balance(user_id)}


@router.post("/accounts/{user_id}/deposit")
def deposit(user_id: int, payload: AmountIn):
    try:
        svc.deposit(user_id, payload.amount_cents, currency=payload.currency)
        return {"balance_cents": svc.get_balance(user_id)}
    except EconomyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/accounts/{user_id}/withdraw")
def withdraw(user_id: int, payload: AmountIn):
    try:
        svc.withdraw(user_id, payload.amount_cents, currency=payload.currency)
        return {"balance_cents": svc.get_balance(user_id)}
    except EconomyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/transfer")
def transfer(payload: TransferIn):
    try:
        svc.transfer(payload.from_user_id, payload.to_user_id, payload.amount_cents, currency=payload.currency)
        return {"ok": True}
    except EconomyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/accounts/{user_id}/transactions", response_model=List[TransactionRecord])
def list_transactions(user_id: int, limit: int = 50):
    return svc.list_transactions(user_id, limit=limit)
