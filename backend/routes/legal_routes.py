"""FastAPI routes for legal dispute management."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.economy_service import EconomyService
from services.legal_service import LegalService
from services.karma_service import KarmaService


class _KarmaDB:
    def __init__(self):
        self.totals = {}
        self.events = []

    def insert_karma_event(self, event):
        self.events.append(event)

    def update_user_karma(self, user_id, amount):
        self.totals[user_id] = self.totals.get(user_id, 0) + amount

    def get_user_karma_total(self, user_id):
        return self.totals.get(user_id, 0)


_economy = EconomyService()
_economy.ensure_schema()
_karma = KarmaService(_KarmaDB())
svc = LegalService(_economy, _karma)

router = APIRouter(prefix="/legal", tags=["Legal"])


class CaseCreateIn(BaseModel):
    plaintiff_id: int
    defendant_id: int
    description: str
    amount_cents: int = 0


@router.post("/cases/create")
def create_case(payload: CaseCreateIn):
    case = svc.create_case(
        plaintiff_id=payload.plaintiff_id,
        defendant_id=payload.defendant_id,
        description=payload.description,
        amount_cents=payload.amount_cents,
    )
    return case.to_dict()


class FilingIn(BaseModel):
    case_id: int
    filer_id: int
    text: str


@router.post("/cases/file")
def file_filing(payload: FilingIn):
    try:
        case = svc.add_filing(payload.case_id, payload.filer_id, payload.text)
    except KeyError:
        raise HTTPException(status_code=404, detail="case not found")
    return case.to_dict()


class VerdictIn(BaseModel):
    case_id: int
    decision: str
    penalty_cents: int = 0


@router.post("/cases/verdict")
def issue_verdict(payload: VerdictIn):
    try:
        case = svc.arbitrate_case(payload.case_id, payload.decision, payload.penalty_cents)
    except KeyError:
        raise HTTPException(status_code=404, detail="case not found")
    return case.to_dict()


class CaseQuery(BaseModel):
    case_id: int


@router.get("/cases/get")
def get_case(payload: CaseQuery):
    case = svc.get_case(payload.case_id)
    if not case:
        raise HTTPException(status_code=404, detail="case not found")
    return case.to_dict()
