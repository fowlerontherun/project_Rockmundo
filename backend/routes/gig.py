from auth.dependencies import get_current_user_id, require_role
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.gig import Gig
from schemas.gig import GigCreate, GigOut
from database import get_db

# Simulated fame and skill lookup (to be replaced with real logic or DB queries)
def get_band_fame(band_id: int, db: Session) -> int:
    return 350  # Simulated fame

def get_band_acoustic_skill_score(band_id: int, db: Session) -> int:
    return 80  # Simulated skill

def is_band_solo(band_id: int, db: Session) -> bool:
    return False  # Simulated solo check

router = APIRouter()

@router.post("/gigs/book", response_model=GigOut, dependencies=[Depends(require_role(["admin", "moderator", "band_member"]))])
def book_gig(gig: GigCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    if gig.acoustic:
        if is_band_solo(gig.band_id, db):
            pass
        else:
            fame = get_band_fame(gig.band_id, db)
            skill = get_band_acoustic_skill_score(gig.band_id, db)
            if fame < 300 or skill < 70:
                raise HTTPException(
                    status_code=403,
                    detail="Band not eligible for acoustic performance (min fame: 300, skill: 70)."
                )

    new_gig = Gig(**gig.dict())
    db.add(new_gig)
    db.commit()
    db.refresh(new_gig)
    return new_gig

@router.get("/gigs/{band_id}", response_model=list[GigOut])
def get_band_gigs(band_id: int, db: Session = Depends(get_db)):
    return db.query(Gig).filter(Gig.band_id == band_id).all()

@router.get("/gigs", response_model=list[GigOut])
def get_all_gigs(db: Session = Depends(get_db)):
    return db.query(Gig).all()