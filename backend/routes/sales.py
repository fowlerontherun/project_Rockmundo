from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models.sales import SalesData
from schemas.sales import SalesCreate
from database import get_db

router = APIRouter()

@router.post("/sales/add", dependencies=[Depends(require_role(["admin", "moderator", "band_member"]))])
def add_sales_data(data: SalesCreate, db: Session = Depends(get_db)):
    new_data = SalesData(**data.dict())
    db.add(new_data)
    db.commit()
    db.refresh(new_data)
    return new_data