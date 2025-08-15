from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.transport import Transport
from schemas.transport import TransportCreate

router = APIRouter()

@router.post("/transport/add", dependencies=[Depends(require_role(["admin", "moderator", "band_member"]))])
def add_transport(transport_data: TransportCreate, db: Session = Depends(get_db)):
    new_vehicle = Transport(**transport_data.dict())
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return new_vehicle

@router.get("/transport/list")
def list_transport(db: Session = Depends(get_db)):
    return db.query(Transport).all()