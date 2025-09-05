# services/lifestyle_service.py

from datetime import datetime
import random

from .skill_service import skill_service

def calculate_lifestyle_score(data):
    # Composite score from normalized attributes
    score = (
        (min(data["sleep_hours"], 8) / 8.0) * 20 +
        (100 - data["stress"]) * 0.15 +
        data["training_discipline"] * 0.15 +
        data["mental_health"] * 0.3 +
        data["nutrition"] * 0.1 +
        data["fitness"] * 0.1
    )
    return round(score, 2)

def evaluate_lifestyle_risks(data):
    events = []
    if data["stress"] > 85 and random.random() < 0.2:
        events.append("burnout")
    if data["drinking"] == "heavy" and random.random() < 0.15:
        events.append("illness")
    if data["sleep_hours"] < 6 and random.random() < 0.2:
        events.append("mental fatigue")
    if data["nutrition"] < 40 and random.random() < 0.1:
        events.append("nutrition deficiency")
    if data["fitness"] < 30 and random.random() < 0.1:
        events.append("injury")
    return events


# ---------------------------------------------------------------------------
# Recovery helpers

_RECOVERY_ACTIONS = {
    "rest": {
        "sleep_hours": 2,  # hours of extra rest
        "stress": -20,
        "burnout": 2,
    },
    "meditate": {
        "stress": -15,
        "mental_health": 5,
        "burnout": 1,
    },
}


def apply_recovery_action(user_id: int, data: dict, action: str) -> dict:
    """Apply a recovery action to lifestyle data and reduce burnout.

    Parameters
    ----------
    user_id: int
        The id of the user taking the action.
    data: dict
        The lifestyle data to mutate.
    action: str
        Name of the recovery action (e.g. ``"rest"`` or ``"meditate"``).
    """

    effects = _RECOVERY_ACTIONS.get(action)
    if not effects:
        return data

    burnout_reduction = effects.get("burnout", 1)

    # Mutate lifestyle attributes within reasonable bounds
    for key, delta in effects.items():
        if key == "burnout":
            continue
        if key == "sleep_hours":
            data[key] = min(12, data.get(key, 0) + delta)
        else:
            data[key] = max(0, min(100, data.get(key, 0) + delta))

    # Recovery actions help relieve burnout from repetitive training
    skill_service.reduce_burnout(user_id, amount=burnout_reduction)

    return data


__all__ = [
    "calculate_lifestyle_score",
    "evaluate_lifestyle_risks",
    "apply_recovery_action",
]
