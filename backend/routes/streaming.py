from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.streaming import DigitalSale, VinylSale, Stream
from schemas.streaming import (
    DigitalSaleCreate, VinylSaleCreate, StreamCreate,
    DigitalSaleOut, VinylSaleOut, StreamOut
)

router = APIRouter()

@router.post("/sales/digital", response_model=DigitalSaleOut)
def record_digital_sale(sale: DigitalSaleCreate, db: Session = Depends(get_db)):
    new_sale = DigitalSale(**sale.dict())
    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)
    return new_sale

@router.post("/sales/vinyl", response_model=VinylSaleOut)
def record_vinyl_sale(sale: VinylSaleCreate, db: Session = Depends(get_db)):
    new_sale = VinylSale(**sale.dict())
    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)
    return new_sale

@router.post("/streams", response_model=StreamOut)
def record_stream(data: StreamCreate, db: Session = Depends(get_db)):
    new_stream = Stream(**data.dict())
    db.add(new_stream)
    db.commit()
    db.refresh(new_stream)
    return new_stream