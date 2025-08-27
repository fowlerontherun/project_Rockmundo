from auth.dependencies import get_current_user_id, require_role
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.band import Band, BandMember, BandCollaboration
from schemas.band import (
    BandCreate, BandResponse,
    BandMemberInvite,
    BandCollaborationCreate, BandCollaborationResponse
)
from database import get_db
from utils.i18n import _

router = APIRouter(prefix="/bands", tags=["Bands"])

@router.post("/", response_model=BandResponse, dependencies=[Depends(require_role(["admin", "moderator", "band_member"]))])
def create_band(band: BandCreate, db: Session = Depends(get_db)):
    existing = db.query(Band).filter_by(name=band.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=_("Band name already exists"))
    new_band = Band(**band.dict())
    db.add(new_band)
    db.commit()
    db.refresh(new_band)

    # Add founder as first member
    db.add(BandMember(
        character_id=band.founder_id,
        band_id=new_band.id,
        role="Founder",
        is_manager=True
    ))
    db.commit()

    return new_band

@router.get("/{band_id}", response_model=BandResponse)
def get_band(band_id: int, db: Session = Depends(get_db)):
    band = db.query(Band).get(band_id)
    if not band:
        raise HTTPException(status_code=404, detail=_("Band not found"))
    return band

@router.post("/invite")
def invite_member(invite: BandMemberInvite, db: Session = Depends(get_db)):
    exists = db.query(BandMember).filter_by(
        character_id=invite.character_id, band_id=invite.band_id
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail=_("Already a band member"))
    db.add(BandMember(**invite.dict()))
    db.commit()
    return {"message": _("Member invited")}

@router.post("/collaborate", response_model=BandCollaborationResponse)
def create_collaboration(collab: BandCollaborationCreate, db: Session = Depends(get_db)):
    if collab.band_1_id == collab.band_2_id:
        raise HTTPException(status_code=400, detail=_("A band cannot collaborate with itself"))
    new_collab = BandCollaboration(**collab.dict())
    db.add(new_collab)
    db.commit()
    db.refresh(new_collab)
    return new_collab

@router.get("/{band_id}/collaborations", response_model=list[BandCollaborationResponse])
def list_collaborations(band_id: int, db: Session = Depends(get_db)):
    return db.query(BandCollaboration).filter(
        (BandCollaboration.band_1_id == band_id) |
        (BandCollaboration.band_2_id == band_id)
    ).all()
