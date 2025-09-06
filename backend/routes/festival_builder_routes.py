from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from auth.dependencies import get_current_user_id, require_permission
from backend.models.festival_builder import FestivalBuilder
from backend.services.festival_builder_service import (
    BookingConflictError,
    FestivalBuilderService,
    FestivalError,
)

router = APIRouter(prefix="/festival-builder", tags=["festival-builder"])
_service = FestivalBuilderService()


# Dependency to allow test overrides
def get_service() -> FestivalBuilderService:
    return _service


# ----------- Admin endpoints -----------
@router.post("/admin/festivals", dependencies=[Depends(require_permission(["admin"]))])
def create_festival(payload: dict, svc: FestivalBuilderService = Depends(get_service)) -> dict:
    fid = svc.create_festival(
        name=payload["name"],
        owner_id=payload.get("owner_id", 0),
        stages=payload.get("stages", {}),
        ticket_tiers=payload.get("ticket_tiers", []),
        sponsors=payload.get("sponsors"),
    )
    fest = svc.get_festival(fid)
    return {"id": fest.id, "name": fest.name}


@router.post(
    "/admin/festivals/{festival_id}/book",
    dependencies=[Depends(require_permission(["admin"]))],
)
def book_act(
    festival_id: int,
    payload: dict,
    svc: FestivalBuilderService = Depends(get_service),
) -> dict:
    try:
        svc.book_act(
            festival_id=festival_id,
            stage_name=payload["stage"],
            slot_index=int(payload["slot"]),
            band_id=int(payload["band_id"]),
            payout_cents=int(payload.get("payout_cents", 0)),
        )
        return {"status": "ok"}
    except BookingConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except FestivalError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/admin/festivals/{festival_id}/finances",
    dependencies=[Depends(require_permission(["admin"]))],
)
def get_finances(
    festival_id: int, svc: FestivalBuilderService = Depends(get_service)
) -> dict:
    return svc.get_finances(festival_id)


# ----------- Player endpoints -----------
@router.get("/player/festivals/{festival_id}")
def get_festival(
    festival_id: int, svc: FestivalBuilderService = Depends(get_service)
) -> FestivalBuilder:
    try:
        return svc.get_festival(festival_id)
    except FestivalError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/player/festivals/{festival_id}/tickets")
def purchase_tickets(
    festival_id: int,
    payload: dict,
    user_id: int = Depends(get_current_user_id),
    svc: FestivalBuilderService = Depends(get_service),
) -> dict:
    try:
        revenue = svc.sell_tickets(
            festival_id, payload["tier"], int(payload.get("qty", 1)), user_id
        )
        return {"revenue": revenue}
    except FestivalError as e:
        raise HTTPException(status_code=400, detail=str(e))
