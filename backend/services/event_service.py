# services/event_service.py
import logging
import random
import sqlite3
from typing import Dict, List

from seeds.skill_seed import SKILL_NAME_TO_ID

from backend.database import DB_PATH
from backend.models.event import Event
from backend.models.event_effect import EventEffect
from backend.models.npc import NPC
from backend.models.skill import Skill

from .city_service import city_service
from .npc_ai_service import npc_ai_service
from .skill_service import skill_service
from .weather_service import weather_service

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
                skill_id INTEGER,
                start_date TEXT NOT NULL,
                duration_days INTEGER NOT NULL
            )
            """
        )
        conn.commit()


def roll_for_daily_event(user_id, lifestyle_data, active_skills):
    """Determine if a daily event triggers for the user."""

    vocals_id = SKILL_NAME_TO_ID["vocals"]
    guitar_id = SKILL_NAME_TO_ID["guitar"]

    # Sample logic: if drinking high and vocals practiced 5 days in a row
    if lifestyle_data.get("drinking") == "high" and vocals_id in active_skills:
        if random.random() < 0.15:
            return {
                "event": "vocal fatigue",
                "effect": "freeze_progress",
                "skill_id": vocals_id,
                "duration": 3,
            }

    if random.random() < 0.01:
        return {
            "event": "sprained wrist",
            "effect": "block_skill",
            "skill_id": guitar_id,
            "duration": 5,
        }

    return None


def roll_for_npc_daily_events(npc: NPC, lifestyle_data=None):
    """Generate daily NPC events via the AI service."""
    lifestyle_data = lifestyle_data or {}
    return npc_ai_service.generate_daily_behavior(npc, lifestyle_data)


def apply_event_effect(user_id, event_data):
    _ensure_schema()
    effect = EventEffect(
        user_id=user_id,
        effect=event_data.get("effect"),
        duration=event_data.get("duration", 0),
        skill_id=event_data.get("skill_id"),
    )
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO event_effects (user_id, effect, skill_id, start_date, duration_days)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                effect.user_id,
                effect.effect,
                effect.skill_id,
                effect.start,
                effect.duration,
            ),
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


def is_skill_blocked(user_id, skill_id: int):
    _ensure_schema()
    with _conn() as conn:
        cur = conn.execute(
            """
            SELECT 1 FROM event_effects
             WHERE user_id = ? AND skill_id = ? AND effect = 'block_skill'
               AND datetime(start_date, '+' || duration_days || ' days') > datetime('now')
            """,
            (user_id, skill_id),
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


# ---------------------------------------------------------------------------
# Workshop events
# ---------------------------------------------------------------------------

_workshops: Dict[int, Event] = {}


def schedule_workshop(event: Event) -> Event:
    """Add a workshop to the upcoming schedule."""

    _workshops[event.id] = event
    return event


def list_workshops() -> List[Event]:
    """Return all scheduled workshops."""

    return list(_workshops.values())


def clear_workshops() -> None:
    """Testing helper to clear registered workshops."""

    _workshops.clear()


def purchase_workshop_ticket(user_id: int, event_id: int) -> Event:
    """Register a user for a workshop and award XP."""

    workshop = _workshops.get(event_id)
    if workshop is None:
        raise ValueError("workshop not found")
    if user_id in workshop.attendees:
        raise ValueError("already registered")
    if not workshop.has_space():
        raise ValueError("workshop full")

    workshop.attendees.append(user_id)

    skill_id = SKILL_NAME_TO_ID.get(workshop.skill_target, 0)
    skill = Skill(id=skill_id, name=workshop.skill_target, category="event")
    skill_service.train(user_id, skill, workshop.xp_reward)
    return workshop
