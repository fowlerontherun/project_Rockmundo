from auth.dependencies import get_current_user_id, require_role
# File: backend/routes/sponsorship.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os

# Import style chosen to match many existing projects where routes/ and services/ are siblings
from services.sponsorship_service import SponsorshipService

router = APIRouter(prefix="/api/sponsorships", tags=["Sponsorships"])

def get_service() -> SponsorshipService:
    # Use env var if present, else default SQLite in CWD
    db_path = os.environ.get("DEVMIND_DB_PATH") or "devmind_schema.db"
    return SponsorshipService(db_path)

# ---------- Models ----------
class SponsorIn(BaseModel):
    
name: str
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    contact_email: Optional[str] = None
    notes: Optional[str] = None

class VenueSponsorshipIn(BaseModel):
    
venue_id: int
    sponsor_id: int
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="YYYY-MM-DD or null")
    is_active: bool = True
    naming_format: Optional[str] = "{sponsor} {venue}"
    show_logo: bool = True
    show_website: bool = True
    revenue_model: str = "CPM"
    revenue_cents_per_unit: Optional[int] = None
    fixed_fee_cents: Optional[int] = None
    currency: str = "USD"

class AdEventIn(BaseModel):
    
sponsorship_id: int
    event_type: str  # 'impression' | 'click'
    meta_json: Optional[str] = None

# ---------- Sponsor admin ----------
@router.post("/admin/sponsors", response_model=Dict[str, int])
async def create_sponsor(payload: SponsorIn, svc: SponsorshipService = Depends(get_service)):
    sponsor_id = await svc.create_sponsor(payload.dict())
    return {"id": sponsor_id}

@router.get("/admin/sponsors", response_model=List[Dict[str, Any]])
async def list_sponsors(svc: SponsorshipService = Depends(get_service)):
    return await svc.list_sponsors()

@router.patch("/admin/sponsors/{sponsor_id}")
async def update_sponsor(sponsor_id: int, payload: Dict[str, Any], svc: SponsorshipService = Depends(get_service)):
    await svc.update_sponsor(sponsor_id, payload)
    return {"ok": True}

@router.delete("/admin/sponsors/{sponsor_id}")
async def delete_sponsor(sponsor_id: int, svc: SponsorshipService = Depends(get_service)):
    await svc.delete_sponsor(sponsor_id)
    return {"ok": True}

# ---------- Venue sponsorship admin ----------
@router.post("/admin/venue", response_model=Dict[str, int])
async def create_venue_sponsorship(payload: VenueSponsorshipIn, svc: SponsorshipService = Depends(get_service)):
    sponsorship_id = await svc.create_venue_sponsorship(payload.dict())
    return {"id": sponsorship_id}

@router.get("/admin/venue", response_model=List[Dict[str, Any]])
async def list_venue_sponsorships(venue_id: Optional[int] = None, active_only: bool = False, svc: SponsorshipService = Depends(get_service)):
    return await svc.list_venue_sponsorships(venue_id=venue_id, active_only=active_only)

@router.patch("/admin/venue/{sponsorship_id}")
async def update_venue_sponsorship(sponsorship_id: int, payload: Dict[str, Any], svc: SponsorshipService = Depends(get_service)):
    await svc.update_venue_sponsorship(sponsorship_id, payload)
    return {"ok": True}

@router.post("/admin/venue/{sponsorship_id}/end")
async def end_venue_sponsorship(sponsorship_id: int, end_date: Optional[str] = None, svc: SponsorshipService = Depends(get_service)):
    await svc.end_venue_sponsorship(sponsorship_id, end_date)
    return {"ok": True}

# ---------- Public helpers ----------
@router.get("/venue/{venue_id}")
async def get_venue_with_sponsorship(venue_id: int, svc: SponsorshipService = Depends(get_service)):
    try:
        return await svc.get_venue_with_sponsorship(venue_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Venue not found")

# ---------- Tracking ----------
@router.post("/events")
async def record_ad_event(payload: AdEventIn, svc: SponsorshipService = Depends(get_service)):
    await svc.record_ad_event(payload.sponsorship_id, payload.event_type, payload.meta_json)
    return {"ok": True}

@router.get("/events/{sponsorship_id}/rollup")
async def ad_rollup(sponsorship_id: int, svc: SponsorshipService = Depends(get_service)):
    return await svc.get_ad_rollup(sponsorship_id)
