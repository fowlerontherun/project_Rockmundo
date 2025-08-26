from auth.dependencies import get_current_user_id, require_role
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.distribution import SongDistribution
from models.music import Song
from schemas.distribution import DistributionUpdate, DistributionResponse

router = APIRouter(prefix="/distribution", tags=["Distribution"])

STREAM_RATE = 0.005  # $0.005 per stream
DIGITAL_PRICE = 1.29  # $1.29 per sale
VINYL_PRICE = 20.00   # $20 per vinyl

@router.post("/update", response_model=DistributionResponse, dependencies=[Depends(require_role(["admin", "moderator", "band_member"]))])
def update_distribution(data: DistributionUpdate, db: Session = Depends(get_db)):
    dist = db.query(SongDistribution).filter_by(song_id=data.song_id).first()
    if not dist:
        dist = SongDistribution(song_id=data.song_id)
        db.add(dist)

    # Add new counts
    dist.streams += data.streams
    dist.digital_sales += data.digital_sales
    dist.vinyl_sales += data.vinyl_sales

    # Update costs
    if data.digital_cost:
        dist.digital_cost = data.digital_cost
    if data.vinyl_cost:
        dist.vinyl_cost = data.vinyl_cost

    # Revenue calculations
    dist.streaming_revenue = dist.streams * STREAM_RATE
    dist.digital_revenue = (dist.digital_sales * DIGITAL_PRICE) - dist.digital_cost
    dist.vinyl_revenue = (dist.vinyl_sales * VINYL_PRICE) - dist.vinyl_cost

    db.commit()
    db.refresh(dist)
    return dist

@router.get("/earnings/{song_id}", response_model=DistributionResponse)
def get_song_earnings(song_id: int, db: Session = Depends(get_db)):
    dist = db.query(SongDistribution).filter_by(song_id=song_id).first()
    if not dist:
        raise HTTPException(status_code=404, detail="No earnings recorded for this song")
    return dist

@router.get("/charts")
def get_global_charts(db: Session = Depends(get_db)):
    rows = db.query(SongDistribution).all()
    combined = sorted(rows, key=lambda x: (
        x.streaming_revenue + x.digital_revenue + x.vinyl_revenue
    ), reverse=True)
    streaming = sorted(rows, key=lambda x: x.streams, reverse=True)
    digital = sorted(rows, key=lambda x: x.digital_sales, reverse=True)
    vinyl = sorted(rows, key=lambda x: x.vinyl_sales, reverse=True)

    return {
        "top_combined": [r.song_id for r in combined[:10]],
        "top_streaming": [r.song_id for r in streaming[:10]],
        "top_digital": [r.song_id for r in digital[:10]],
        "top_vinyl": [r.song_id for r in vinyl[:10]],
    }
