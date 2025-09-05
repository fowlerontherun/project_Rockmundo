# services/lifestyle_service.py

from datetime import datetime, timedelta
import random
import sqlite3

from backend.database import DB_PATH
from backend.models.activity import ExerciseActivity

from .skill_service import skill_service
from .xp_reward_service import xp_reward_service

# ---------------------------------------------------------------------------
# Exercise handling

# Minimum time between exercise sessions to receive full benefits.
EXERCISE_COOLDOWN = timedelta(hours=6)
# Fitness bonus granted when exercising outside the cooldown window.
EXERCISE_FITNESS_BONUS = 5


def log_exercise_session(
    user_id: int,
    minutes: int,
    conn: sqlite3.Connection | None = None,
    activity: ExerciseActivity | None = None,
) -> bool:
    """Record an exercise session and apply fitness gains with cooldown.

    Parameters
    ----------
    user_id: int
        The id of the exercising user.
    minutes: int
        Duration of the session in minutes.
    conn: sqlite3.Connection | None
        Optional existing connection to reuse.

    Returns
    -------
    bool
        ``True`` if the session granted full benefits, ``False`` otherwise.
    """

    now = datetime.utcnow()
    own_conn = conn is None
    if own_conn:
        conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT fitness, exercise_minutes, last_exercise, appearance_score FROM lifestyle WHERE user_id = ?",
        (user_id,),
    )
    row = cur.fetchone()
    if not row:
        if own_conn:
            conn.close()
        return False

    fitness, total_minutes, last, appearance = row
    full_benefit = True
    if last:
        last_dt = datetime.fromisoformat(last)
        if now - last_dt < EXERCISE_COOLDOWN:
            full_benefit = False

    gain = EXERCISE_FITNESS_BONUS if full_benefit else 0
    new_fitness = min(100, fitness + gain)
    bonus = activity.appearance_bonus if activity else 0
    new_appearance = min(100, appearance + bonus)
    cur.execute(
        """
        UPDATE lifestyle
        SET fitness = ?, exercise_minutes = ?, last_exercise = ?, appearance_score = ?
        WHERE user_id = ?
        """,
        (
            new_fitness,
            total_minutes + minutes,
            now.isoformat(),
            new_appearance,
            user_id,
        ),
    )
    conn.commit()
    if own_conn:
        conn.close()
    return full_benefit

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


def grant_daily_xp(
    user_id: int, data: dict, conn: sqlite3.Connection | None = None
) -> int:
    """Grant daily XP based on the user's lifestyle score.

    The ``xp_reward_service`` is used to award XP scaled by the calculated
    lifestyle score. Low scores yield smaller rewards while healthy habits
    grant more XP.  The awarded amount is returned for introspection or
    testing purposes.
    """

    score = calculate_lifestyle_score(data)
    # Scale 0-100 score into a small XP reward range (0-20)
    amount = max(0, int(score / 5))
    try:
        xp_reward_service.grant_hidden_xp(
            user_id, reason="lifestyle", amount=amount, conn=conn
        )
    except Exception:
        pass
    return amount


__all__ = [
    "calculate_lifestyle_score",
    "evaluate_lifestyle_risks",
    "apply_recovery_action",
    "grant_daily_xp",
    "log_exercise_session",
]
