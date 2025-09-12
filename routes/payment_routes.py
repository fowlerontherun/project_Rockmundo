"""FastAPI routes for payment operations."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models.payment import SubscriptionPlan
from services.economy_service import EconomyService
from services.payment_service import (
    PaymentError,
    PaymentGateway,
    PaymentService,
)

router = APIRouter(prefix="/payment", tags=["Payment"])


class MockGateway(PaymentGateway):
    """Simple in-process gateway used for tests and local development."""

    def __init__(self, succeed: bool = True):
        self.succeed = succeed
        self.counter = 0

    def create_payment(self, amount_cents: int, currency: str) -> str:
        self.counter += 1
        return f"pay_{self.counter}"

    def verify_payment(self, payment_id: str) -> bool:
        return self.succeed


# instantiate services
_economy = EconomyService()
_economy.ensure_schema()
_gateway = MockGateway()
svc = PaymentService(_gateway, _economy)


class PurchaseIn(BaseModel):
    user_id: int
    amount_cents: int


class CallbackIn(BaseModel):
    payment_id: str


class SubscriptionIn(BaseModel):
    user_id: int
    plan_id: str


@router.post("/purchase")
def initiate_purchase(payload: PurchaseIn):
    payment_id = svc.initiate_purchase(payload.user_id, payload.amount_cents)
    return {"payment_id": payment_id}


@router.post("/callback")
def verify_callback(payload: CallbackIn):
    try:
        record = svc.verify_callback(payload.payment_id)
        return {"status": record.status}
    except PaymentError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subscribe")
def subscribe(payload: SubscriptionIn):
    plan = SubscriptionPlan(id=payload.plan_id, name=payload.plan_id, price_cents=0, currency="USD", interval="monthly")
    svc.create_subscription(payload.user_id, plan)
    return {"status": "subscribed"}


@router.post("/unsubscribe")
def unsubscribe(payload: SubscriptionIn):
    svc.cancel_subscription(payload.user_id)
    return {"status": "unsubscribed"}
