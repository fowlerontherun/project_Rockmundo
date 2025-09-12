from auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.venues import Venue
from schemas.venues import VenueCreate

router = APIRouter()

@router.post("/venues/add", dependencies=[Depends(require_permission(["admin"]))])
def add_venue(venue_data: VenueCreate, db: Session = Depends(get_db)):
    new_venue = Venue(**venue_data.dict())
    db.add(new_venue)
    db.commit()
    db.refresh(new_venue)
    return new_venue