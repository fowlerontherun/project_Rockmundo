from auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models.awards import SongAward
from schemas.awards import SongAwardCreate
from database import get_db

router = APIRouter()

@router.post("/awards/add")
def add_award(data: SongAwardCreate, db: Session = Depends(get_db)):
    new_award = SongAward(**data.dict())
    db.add(new_award)
    db.commit()
    db.refresh(new_award)
    return new_award