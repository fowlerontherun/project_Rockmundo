from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.tours import Tour, TourStop
from schemas.tours import TourCreate, TourStopCreate
from datetime import datetime

router = APIRouter()

@router.post("/tours/create", dependencies=[Depends(require_role(["admin", "moderator", "band_member"]))])
def create_tour(tour_data: TourCreate, db: Session = Depends(get_db)):
    new_tour = Tour(**tour_data.dict())
    db.add(new_tour)
    db.commit()
    db.refresh(new_tour)
    return new_tour

@router.post("/tours/add_stop")
def add_tour_stop(stop_data: TourStopCreate, db: Session = Depends(get_db)):
    new_stop = TourStop(**stop_data.dict())
    db.add(new_stop)
    db.commit()
    db.refresh(new_stop)
    return new_stop