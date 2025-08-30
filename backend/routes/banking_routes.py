from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.economy_service import EconomyError, EconomyService

router = APIRouter(prefix="/banking", tags=["Banking"])
svc = EconomyService()
svc.ensure_schema()


class LoanIn(BaseModel):
    user_id: int
    amount_cents: int
    interest_rate: float
    term_days: int


class ConversionIn(BaseModel):
    amount_cents: int
    from_currency: str
    to_currency: str


@router.post("/loans")
def create_loan(payload: LoanIn):
    try:
        loan_id = svc.create_loan(
            payload.user_id,
            payload.amount_cents,
            payload.interest_rate,
            payload.term_days,
        )
        return {"loan_id": loan_id}
    except EconomyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/convert")
def convert(payload: ConversionIn):
    try:
        amount = svc.convert_currency(
            payload.amount_cents, payload.from_currency, payload.to_currency
        )
        return {"amount_cents": amount}
    except EconomyError as e:
        raise HTTPException(status_code=400, detail=str(e))
