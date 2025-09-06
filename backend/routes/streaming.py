from auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.streaming import DigitalSale, VinylSale, Stream
from backend.services.streaming_service import perform_live_stream
from schemas.streaming import (
    DigitalSaleCreate,
    VinylSaleCreate,
    StreamCreate,
    DigitalSaleOut,
    VinylSaleOut,
    StreamOut,
    LiveStreamRequest,
    LiveStreamResult,
)


router = APIRouter()


@router.post(
    "/sales/digital",
    response_model=DigitalSaleOut,
    dependencies=[Depends(require_permission(["user", "band_member", "moderator", "admin"]))],
)
def record_digital_sale(sale: DigitalSaleCreate, db: Session = Depends(get_db)):
    new_sale = DigitalSale(**sale.dict())
    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)
    return new_sale


@router.post(
    "/sales/vinyl",
    response_model=VinylSaleOut,
    dependencies=[Depends(require_permission(["user", "band_member", "moderator", "admin"]))],
)
def record_vinyl_sale(sale: VinylSaleCreate, db: Session = Depends(get_db)):
    new_sale = VinylSale(**sale.dict())
    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)
    return new_sale


@router.post(
    "/streams",
    response_model=StreamOut,
    dependencies=[Depends(require_permission(["user", "band_member", "moderator", "admin"]))],
)
def record_stream(data: StreamCreate, db: Session = Depends(get_db)):
    new_stream = Stream(**data.dict())
    db.add(new_stream)
    db.commit()
    db.refresh(new_stream)
    return new_stream


@router.post(
    "/live",
    response_model=LiveStreamResult,
    dependencies=[Depends(require_permission(["user", "band_member", "moderator", "admin"]))],
)
def perform_live_stream_route(
    payload: LiveStreamRequest,
    user_id: int = Depends(get_current_user_id),
):
    """Perform a live stream and gain experience."""

    return perform_live_stream(
        user_id=user_id,
        duration_minutes=payload.duration_minutes,
        base_viewers=payload.viewers,
    )


__all__ = ["router"]

