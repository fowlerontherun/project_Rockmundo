"""Lifestyle routes exposing wellness mechanics."""

from fastapi import APIRouter
from services.lifestyle_service import (
    calculate_lifestyle_score,
    evaluate_lifestyle_risks,
    apply_recovery_action,
)

router = APIRouter()

fake_lifestyle_data = {
    "user_id": 1,
    "sleep_hours": 5,
    "drinking": "heavy",
    "stress": 90,
    "training_discipline": 60,
    "mental_health": 80,
    "nutrition": 30,
    "fitness": 40,
}

@router.get("/lifestyle/me")
def get_lifestyle():
    score = calculate_lifestyle_score(fake_lifestyle_data)
    events = evaluate_lifestyle_risks(fake_lifestyle_data)
    fake_lifestyle_data["lifestyle_score"] = score
    return {
        "lifestyle": fake_lifestyle_data,
        "risk_events": events
    }


@router.post("/lifestyle/recover/{action}")
def recover(action: str):
    apply_recovery_action(fake_lifestyle_data["user_id"], fake_lifestyle_data, action)
    score = calculate_lifestyle_score(fake_lifestyle_data)
    events = evaluate_lifestyle_risks(fake_lifestyle_data)
    fake_lifestyle_data["lifestyle_score"] = score
    return {"lifestyle": fake_lifestyle_data, "risk_events": events}
