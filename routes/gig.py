from auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter, Depends, HTTPException
from services.notifications_service import NotificationsService
from sqlalchemy.orm import Session
from models.gig import Gig
from models.venues import Venue
from schemas.gig import GigCreate, GigOut
from database import get_db
from utils.i18n import _

from services.band_service import BandService
from services.skill_service import skill_service as skill_service_instance
from services.fame_service import FameService
from models.skill import Skill
from seeds.skill_seed import SKILL_NAME_TO_ID

band_service = BandService()
skill_service = skill_service_instance


class _FameDB:
    def get_band_fame_total(self, band_id: int) -> int:
        info = band_service.get_band_info(band_id)
        return info.get("fame", 0) if info else 0


fame_service = FameService(_FameDB())

ACOUSTIC_SKILL = Skill(
    id=SKILL_NAME_TO_ID.get("studio_acoustics", 0),
    name="studio_acoustics",
    category="creative",
)


def get_band_acoustic_skill_score(band_id: int) -> int:
    info = band_service.get_band_info(band_id)
    members = info.get("members", []) if info else []
    if not members:
        return 0
    total = 0
    for m in members:
        total += skill_service.get_skill_level(m["user_id"], ACOUSTIC_SKILL)
    return total // len(members)


def is_band_solo(band_id: int) -> bool:
    info = band_service.get_band_info(band_id)
    members = info.get("members", []) if info else []
    return len(members) <= 1


def band_has_conflict(band_id: int, date, start, end, db: Session) -> bool:
    return (
        db.query(Gig)
        .filter(
            Gig.band_id == band_id,
            Gig.date == date,
            Gig.start_time < end,
            Gig.end_time > start,
        )
        .first()
        is not None
    )


def venue_has_conflict(venue_id: int, date, start, end, db: Session) -> bool:
    return (
        db.query(Gig)
        .filter(
            Gig.venue_id == venue_id,
            Gig.date == date,
            Gig.start_time < end,
            Gig.end_time > start,
        )
        .first()
        is not None
    )


def get_venue_capacity(venue_id: int, db: Session) -> int:
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail=_("Venue not found"))
    return venue.capacity

router = APIRouter()
notif_svc = NotificationsService()

@router.post(
    "/gigs/book",
    response_model=GigOut,
    dependencies=[Depends(require_permission(["admin", "moderator", "band_member"]))],
)
def book_gig(
    gig: GigCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Create a gig with eligibility, conflict and payout checks."""

    # Acoustic eligibility using real services
    if gig.acoustic:
        if is_band_solo(gig.band_id):
            skill = get_band_acoustic_skill_score(gig.band_id)
            if skill < 70:
                raise HTTPException(
                    status_code=403,
                    detail=_("Band not eligible for acoustic performance (min skill: 70)."),
                )
        else:
            fame = fame_service.get_total_fame(gig.band_id)
            skill = get_band_acoustic_skill_score(gig.band_id)
            if fame < 300 or skill < 70:
                raise HTTPException(
                    status_code=403,
                    detail=_("Band not eligible for acoustic performance (min fame: 300, skill: 70)."),
                )

    # Date/time conflict checks
    if band_has_conflict(gig.band_id, gig.date, gig.start_time, gig.end_time, db):
        raise HTTPException(status_code=400, detail=_("Band already has a gig at that time."))
    if venue_has_conflict(gig.venue_id, gig.date, gig.start_time, gig.end_time, db):
        raise HTTPException(status_code=400, detail=_("Venue is not available at that time."))

    # Capacity and payout calculations
    capacity = get_venue_capacity(gig.venue_id, db)
    expected = gig.expected_audience or capacity
    if expected > capacity:
        raise HTTPException(status_code=400, detail=_("Expected audience exceeds venue capacity."))

    payout = gig.guarantee + expected * gig.ticket_price * gig.ticket_split
    xp_gain = expected // 10
    fans_gain = expected // 5

    data = gig.dict()
    data.pop("expected_audience", None)
    new_gig = Gig(
        **data,
        audience_size=expected,
        total_earned=payout,
        xp_gained=xp_gain,
        fans_gained=fans_gain,
    )
    db.add(new_gig)
    db.commit()
    db.refresh(new_gig)

    # Persist notification for booking confirmation
    try:
        notif_svc.create(
            user_id,
            "Gig booked",
            f"Band {gig.band_id} at venue {gig.venue_id} on {gig.date}",
            type_="gig",
        )
    except Exception:
        pass

    return new_gig

@router.get("/gigs/{band_id}", response_model=list[GigOut])
def get_band_gigs(band_id: int, db: Session = Depends(get_db)):
    return db.query(Gig).filter(Gig.band_id == band_id).all()

@router.get("/gigs", response_model=list[GigOut])
def get_all_gigs(db: Session = Depends(get_db)):
    return db.query(Gig).all()
