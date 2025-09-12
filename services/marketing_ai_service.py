from datetime import date, timedelta
from typing import Dict, List

from backend.models.promotion import Promotion

# In-memory storage for accepted promotions
_promotions_db: List[Promotion] = []
_promo_id: int = 1


def generate_promotion_plan(band_id: int) -> Dict[str, object]:
    """Recommend a simple campaign plan for the band."""
    today = date.today()
    plan = [
        {"type": "tiktok", "date": today.isoformat(), "media_channel": "TikkaTok"},
        {
            "type": "radio",
            "date": (today + timedelta(days=7)).isoformat(),
            "media_channel": "Local Radio",
        },
    ]
    return {"band_id": band_id, "plan": plan}


def accept_promotion_plan(plan: Dict[str, object]) -> Dict[str, object]:
    """Persist accepted plan elements into Promotion models for tracking."""
    global _promo_id
    accepted: List[Promotion] = []
    band_id = int(plan.get("band_id", 0))
    for item in plan.get("plan", []):
        promo = Promotion(
            id=_promo_id,
            band_id=band_id,
            type=item.get("type", "unknown"),
            date=date.fromisoformat(item.get("date")),
            outcome="pending",
            fame_change=0.0,
            fan_gain=0,
            press_score_change=0.0,
            controversy_level=0.0,
            media_channel=item.get("media_channel"),
        )
        _promotions_db.append(promo)
        accepted.append(promo)
        _promo_id += 1
    return {"accepted": len(accepted), "promotions": [p.dict() for p in accepted]}


def list_accepted_promotions() -> List[Promotion]:
    """Return all accepted promotions for inspection/testing."""
    return _promotions_db
