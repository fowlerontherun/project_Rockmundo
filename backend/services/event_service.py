# services/event_service.py
import random
import sqlite3
import logging

from backend.database import DB_PATH
from backend.models.event_effect import EventEffect
from .weather_service import weather_service
from .city_service import city_service

logger = logging.getLogger(__name__)


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(str(DB_PATH))


def _ensure_schema() -> None:
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS event_effects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                effect TEXT NOT NULL,
                skill TEXT,
                start_date TEXT NOT NULL,
                duration_days INTEGER NOT NULL
            )
            """
        )
        conn.commit()


def roll_for_daily_event(user_id, lifestyle_data, active_skills):
    # Sample logic: if drinking high and vocals practiced 5 days in a row
    if lifestyle_data.get("drinking") == "high" and "vocals" in active_skills:
        if random.random() < 0.15:
            return {
                "event": "vocal fatigue",
                "effect": "freeze_progress",
                "skill": "vocals",
                "duration": 3,
            }

    if random.random() < 0.01:
        return {
            "event": "sprained wrist",
            "effect": "block_skill",
            "skill": "guitar",
            "duration": 5,
        }

    return None


def apply_event_effect(user_id, event_data):
    _ensure_schema()
    effect = EventEffect(
        user_id=user_id,
        effect=event_data.get("effect"),
        duration=event_data.get("duration", 0),
        skill=event_data.get("skill"),
    )
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO event_effects (user_id, effect, skill, start_date, duration_days)
            VALUES (?, ?, ?, ?, ?)
            """,
            (effect.user_id, effect.effect, effect.skill, effect.start, effect.duration),
        )
        conn.commit()
    logger.info("Applied %s to user %s", event_data, user_id)


def clear_expired_events() -> int:
    _ensure_schema()
    with _conn() as conn:
        cur = conn.execute(
            """
            DELETE FROM event_effects
            WHERE datetime(start_date, '+' || duration_days || ' days') <= datetime('now')
            """
        )
        conn.commit()
        return cur.rowcount if cur.rowcount is not None else 0


def is_skill_blocked(user_id, skill):
    _ensure_schema()
    with _conn() as conn:
        cur = conn.execute(
            """
            SELECT 1 FROM event_effects
             WHERE user_id = ? AND skill = ? AND effect = 'block_skill'
               AND datetime(start_date, '+' || duration_days || ' days') > datetime('now')
            """,
            (user_id, skill),
        )
        return cur.fetchone() is not None



def adjust_event_attendance(base_attendance: int, region: str) -> int:
    """Modify event attendance based on weather and city trends."""
    forecast = weather_service.get_forecast(region)
    attendance = base_attendance
    if forecast.event and forecast.event.type == "storm":
        attendance = int(attendance * 0.7)
    elif forecast.event and forecast.event.type == "festival":
        attendance = int(attendance * 1.3)
    # apply city economic modifier
    attendance = int(attendance * city_service.get_event_modifier(region))
    return attendance
