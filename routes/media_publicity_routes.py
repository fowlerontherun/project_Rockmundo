from backend.auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter, HTTPException
from models import media_publicity_models
from schemas import media_publicity_schemas
from database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends

router = APIRouter()

@router.post("/event/", dependencies=[Depends(require_permission(["admin"]))])
def create_media_event(event: media_publicity_schemas.MediaEventCreate, db: Session = Depends(get_db)):
    db_event = media_publicity_models.MediaEvent(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.get("/events/")
def list_events(db: Session = Depends(get_db)):
    return db.query(media_publicity_models.MediaEvent).all()
