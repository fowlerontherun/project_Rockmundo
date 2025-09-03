from auth.dependencies import get_current_user_id, require_role
from fastapi import APIRouter, Depends, HTTPException

from schemas.band import (
    BandCreate,
    BandResponse,
    BandMemberInvite,
    BandCollaborationCreate,
    BandCollaborationResponse,
)
from services import band_service
from utils.i18n import _

router = APIRouter(prefix="/bands", tags=["Bands"])

@router.post(
    "/",
    response_model=BandResponse,
    dependencies=[Depends(require_role(["admin", "moderator", "band_member"]))],
)
def create_band(band: BandCreate):
    created = band_service.create_band(band.founder_id, band.name, band.genre)
    return BandResponse(
        id=created.id,
        name=created.name,
        founder_id=created.founder_id,
        genre=created.genre,
        formed_at=created.formed_at,
    )

@router.get("/{band_id}", response_model=BandResponse)
def get_band(band_id: int):
    info = band_service.get_band_info(band_id)
    if not info:
        raise HTTPException(status_code=404, detail=_("Band not found"))
    return BandResponse(
        id=info["id"],
        name=info["name"],
        founder_id=info["founder_id"],
        genre=info["genre"],
        formed_at=info["formed_at"],
    )

@router.post("/invite")
def invite_member(invite: BandMemberInvite):
    band_service.add_member(invite.band_id, invite.character_id, invite.role)
    return {"message": _("Member invited")}

@router.post("/collaborate", response_model=BandCollaborationResponse)
def create_collaboration(collab: BandCollaborationCreate):
    if collab.band_1_id == collab.band_2_id:
        raise HTTPException(status_code=400, detail=_("A band cannot collaborate with itself"))
    return band_service.create_collaboration(
        collab.band_1_id, collab.band_2_id, collab.project_type, collab.title
    )

@router.get("/{band_id}/collaborations", response_model=list[BandCollaborationResponse])
def list_collaborations(band_id: int):
    return band_service.list_collaborations(band_id)


@router.get("/", response_model=list[BandResponse])
def search_bands(search: str = "", page: int = 1, limit: int = 10):
    return band_service.search_bands(search, page, limit)
