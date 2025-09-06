from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl

try:
    from auth.dependencies import get_current_user_id, require_permission
except Exception:  # pragma: no cover
    def require_permission(_: List[str]):
        async def _noop() -> None:  # type: ignore[return-value]
            return None

        return _noop

    async def get_current_user_id() -> int:  # type: ignore[misc]
        return 0

from services.venue_sponsorships_service import (
    SponsorshipIn,
    VenueSponsorshipError,
    VenueSponsorshipsService,
)

router = APIRouter(prefix="/venues/sponsorships", tags=["Venue Sponsorships"])
svc = VenueSponsorshipsService()
svc.ensure_schema()


class SponsorshipInModel(BaseModel):
    venue_id: int
    sponsor_name: str
    sponsor_website: Optional[HttpUrl] = None
    sponsor_logo_url: Optional[HttpUrl] = None
    naming_pattern: str = "{sponsor} {venue}"
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None  # YYYY-MM-DD
    is_active: bool = True


@router.post("", dependencies=[Depends(require_permission(["admin", "moderator"]))])
async def upsert_sponsorship(payload: SponsorshipInModel) -> Dict[str, int]:
    """Create or update a sponsorship for a venue."""

    try:
        sid = svc.upsert_sponsorship(SponsorshipIn(**payload.model_dump()))
    except VenueSponsorshipError as exc:  # pragma: no cover - thin wrapper
        raise HTTPException(status_code=400, detail=str(exc))
    return {"sponsorship_id": sid}


@router.get(
    "/{venue_id}",
    dependencies=[Depends(require_permission(["admin", "moderator", "band_member"]))],
)
async def get_sponsorship(venue_id: int) -> Dict[str, Any]:
    """Retrieve sponsorship details for a venue."""

    sponsorship = svc.get_sponsorship(venue_id)
    if not sponsorship:
        raise HTTPException(status_code=404, detail="No sponsorship set for this venue")
    return sponsorship


@router.post(
    "/{venue_id}/deactivate",
    dependencies=[Depends(require_permission(["admin", "moderator"]))],
)
async def deactivate_sponsorship(venue_id: int) -> Dict[str, bool]:
    """Deactivate a sponsorship for a venue."""

    try:
        svc.deactivate(venue_id)
    except VenueSponsorshipError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"ok": True}


class BrandingQuery(BaseModel):
    venue_name: str
    on_date: Optional[str] = None


@router.post(
    "/{venue_id}/branding",
    dependencies=[Depends(require_permission(["admin", "moderator", "band_member"]))],
)
async def effective_branding(venue_id: int, query: BrandingQuery) -> Dict[str, Any]:
    """Return the effective branding for a venue."""

    return svc.effective_branding(venue_id, query.venue_name, query.on_date)


class NegotiationTerms(BaseModel):
    sponsor_website: Optional[HttpUrl] = None
    sponsor_logo_url: Optional[HttpUrl] = None
    naming_pattern: str = "{sponsor} {venue}"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: bool = True


class OfferIn(BaseModel):
    venue_id: int
    sponsor_name: str
    terms: NegotiationTerms


class CounterIn(BaseModel):
    terms: NegotiationTerms


@router.post(
    "/negotiations/offer",
    dependencies=[Depends(require_permission(["admin", "moderator"]))],
)
async def create_offer(payload: OfferIn) -> Dict[str, Any]:
    negotiation = svc.create_offer(payload.venue_id, payload.sponsor_name, payload.terms.model_dump())
    return negotiation.__dict__


@router.post(
    "/negotiations/{negotiation_id}/counter",
    dependencies=[Depends(require_permission(["admin", "moderator"]))],
)
async def counter_offer(negotiation_id: int, payload: CounterIn) -> Dict[str, Any]:
    try:
        negotiation = svc.counter_offer(negotiation_id, payload.terms.model_dump())
    except VenueSponsorshipError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return negotiation.__dict__


@router.post(
    "/negotiations/{negotiation_id}/accept",
    dependencies=[Depends(require_permission(["admin", "moderator"]))],
)
async def accept_offer(negotiation_id: int) -> Dict[str, Any]:
    try:
        negotiation = svc.accept_offer(negotiation_id)
    except VenueSponsorshipError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return negotiation.__dict__


class ImpressionIn(BaseModel):
    sponsorship_id: int
    placement: Optional[str] = None
    event_id: Optional[int] = None
    meta: Optional[Dict[str, Any]] = None


@router.post(
    "/impressions",
    dependencies=[Depends(require_permission(["admin", "moderator", "band_member"]))],
)
async def record_impression(
    payload: ImpressionIn, user_id: int = Depends(get_current_user_id)
) -> Dict[str, int]:
    """Record an ad impression for a sponsorship."""

    iid = svc.record_impression(
        sponsorship_id=payload.sponsorship_id,
        placement=payload.placement,
        user_id=user_id,
        event_id=payload.event_id,
        meta=payload.meta,
    )
    return {"impression_id": iid}


@router.get(
    "/impressions/{sponsorship_id}",
    dependencies=[Depends(require_permission(["admin", "moderator"]))],
)
async def list_impressions(
    sponsorship_id: int, limit: int = 100
) -> List[Dict[str, Any]]:
    """List ad impressions for a sponsorship."""

    return svc.list_impressions(sponsorship_id, limit)

