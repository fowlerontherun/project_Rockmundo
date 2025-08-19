# File: backend/routes/venue_sponsorships_routes.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from services.venue_sponsorships_service import VenueSponsorshipsService, VenueSponsorshipError, SponsorshipIn

# Auth dependency
try:
    from auth.dependencies import require_role
except Exception:
    def require_role(roles):
        async def _noop():
            return True
        return _noop

router = APIRouter(prefix="/venues/sponsorships", tags=["Venue Sponsorships"])
svc = VenueSponsorshipsService()
svc.ensure_schema()

class SponsorshipInModel(BaseModel):
    venue_id: int
    sponsor_name: str
    sponsor_website: Optional[str] = None
    sponsor_logo_url: Optional[str] = None
    naming_pattern: Optional[str] = "{sponsor} {venue}"
    start_date: Optional[str] = None    # YYYY-MM-DD
    end_date: Optional[str] = None      # YYYY-MM-DD
    is_active: bool = True

@router.post("", dependencies=[Depends(require_role(["admin", "moderator"]))])
def upsert_sponsorship(payload: SponsorshipInModel):
    try:
        sid = svc.upsert_sponsorship(SponsorshipIn(**payload.model_dump()))
        return {"sponsorship_id": sid}
    except VenueSponsorshipError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{venue_id}", dependencies=[Depends(require_role(["admin", "moderator", "band_member"]))])
def get_sponsorship(venue_id: int):
    s = svc.get_sponsorship(venue_id)
    if not s:
        raise HTTPException(status_code=404, detail="No sponsorship set for this venue")
    return s

@router.post("/{venue_id}/deactivate", dependencies=[Depends(require_role(["admin", "moderator"]))])
def deactivate(venue_id: int):
    try:
        svc.deactivate(venue_id)
        return {"ok": True}
    except VenueSponsorshipError as e:
        raise HTTPException(status_code=400, detail=str(e))

class BrandingQuery(BaseModel):
    venue_name: str
    on_date: Optional[str] = None

@router.post("/{venue_id}/branding", dependencies=[Depends(require_role(["admin", "moderator", "band_member"]))])
def effective_branding(venue_id: int, query: BrandingQuery):
    return svc.effective_branding(venue_id, query.venue_name, query.on_date)

# ---- Ad Impressions ----
class ImpressionIn(BaseModel):
    sponsorship_id: int
    placement: Optional[str] = None
    user_id: Optional[int] = None
    event_id: Optional[int] = None
    meta: Optional[Dict[str, Any]] = None

@router.post("/impressions", dependencies=[Depends(require_role(["admin", "moderator", "band_member"]))])
def record_impression(payload: ImpressionIn):
    iid = svc.record_impression(
        sponsorship_id=payload.sponsorship_id,
        placement=payload.placement,
        user_id=payload.user_id,
        event_id=payload.event_id,
        meta=payload.meta,
    )
    return {"impression_id": iid}

@router.get("/impressions/{sponsorship_id}", dependencies=[Depends(require_role(["admin", "moderator"]))])
def list_impressions(sponsorship_id: int, limit: int = 100):
    return svc.list_impressions(sponsorship_id, limit)
