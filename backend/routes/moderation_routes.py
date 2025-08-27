from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.moderation_service import ModerationService, moderation_service

router = APIRouter(prefix="/moderation", tags=["Moderation"])

svc: ModerationService = moderation_service


class ReportIn(BaseModel):
    reporter_id: int
    target_id: int
    reason: str


class SanctionIn(BaseModel):
    type: str
    reason: str
    duration_hours: Optional[int] = None


@router.post("/reports")
def submit_report(payload: ReportIn):
    report = svc.handle_report(payload.reporter_id, payload.target_id, payload.reason)
    return report.to_dict()


@router.get("/reports")
def list_pending_reports():
    return [r.to_dict() for r in svc.get_pending_reports()]


@router.post("/reports/{report_id}/sanction")
def sanction_report(report_id: int, payload: SanctionIn):
    try:
        report = svc.resolve_report(report_id, "sanction", payload.type)
        return report.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
