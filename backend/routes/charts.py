from auth.dependencies import get_current_user_id, require_role
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models.charts import ChartEntry
from schemas.charts import ChartEntryCreate
from database import get_db

router = APIRouter()

@router.post("/charts/add", dependencies=[Depends(require_role(["user", "band_member", "moderator", "admin"]))])
def add_chart_entry(entry: ChartEntryCreate, db: Session = Depends(get_db)):
    new_entry = ChartEntry(**entry.dict())
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry