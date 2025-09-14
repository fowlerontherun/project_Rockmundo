# services/event_service.py
import json
import logging
import random
import sqlite3
from typing import Any, Dict, List

from seeds.skill_seed import SKILL_NAME_TO_ID

from database import DB_PATH
from backend.models.event import Event
from backend.models.event_effect import EventEffect
from backend.models.npc import NPC
from backend.models.skill import Skill

from .city_service import city_service
from .npc_ai_service import npc_ai_service
from .skill_service import skill_service
from .weather_service import weather_service
from .reputation_service import reputation_service

logger = logging.getLogger(__name__)
ELITE_REPUTATION_THRESHOLD = 100


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


def roll_for_daily_event(user_id, lifestyle_data, active_skills, *, luck: int = 0):
    """Determine if a daily event triggers for the user.

    ``luck`` scales the probability of negative outcomes. A higher value
    reduces the chance of detrimental events.
    """

    vocals_id = SKILL_NAME_TO_ID["vocals"]
    guitar_id = SKILL_NAME_TO_ID["guitar"]

    # Sample logic: if drinking high and vocals practiced 5 days in a row
    luck_factor = max(0.0, 1 - luck / 100)
    if lifestyle_data.get("drinking") == "high" and vocals_id in active_skills:
        if random.random() < 0.15 * luck_factor:
            return {
                "event": "vocal fatigue",
                "effect": "freeze_progress",
                "skill_id": vocals_id,
                "duration": 3,
            }

    if random.random() < 0.01 * luck_factor:
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
# Shop events
# ---------------------------------------------------------------------------


def _ensure_shop_event_schema() -> None:
    """Create the table storing scheduled shop events."""
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shop_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                banner TEXT NOT NULL,
                shop_id INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                inventory_json TEXT,
                price_modifier REAL NOT NULL DEFAULT 1.0,
                active INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()


def schedule_shop_event(data: Dict[str, Any]) -> Dict[str, Any]:
    """Persist a shop event and schedule start/end tasks."""

    _ensure_shop_event_schema()
    inventory_json = json.dumps(data.get("inventory", {}))
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO shop_events
            (name, banner, shop_id, start_time, end_time, inventory_json, price_modifier)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["name"],
                data.get("banner", ""),
                data["shop_id"],
                data["start_time"],
                data["end_time"],
                inventory_json,
                float(data.get("price_modifier", 1.0)),
            ),
        )
        event_id = cur.lastrowid
        conn.commit()

    from .scheduler_service import schedule_task  # local import to avoid cycle

    schedule_task(
        "shop_event_start",
        {"event_id": event_id},
        data["start_time"],
    )
    schedule_task(
        "shop_event_end",
        {"event_id": event_id},
        data["end_time"],
    )
    return {"status": "scheduled", "event_id": event_id}


def _apply_inventory(conn: sqlite3.Connection, shop_id: int, items: Dict[str, int]) -> None:
    cur = conn.cursor()
    for item_id, qty in items.items():
        cur.execute(
            """
            UPDATE shop_items
               SET quantity = quantity + ?
             WHERE shop_id = ? AND item_id = ?
            """,
            (qty, shop_id, int(item_id)),
        )


def start_shop_event(event_id: int) -> Dict[str, str]:
    """Handler to activate a shop event."""

    _ensure_shop_event_schema()
    with _conn() as conn:
        cur = conn.execute(
            "SELECT shop_id, inventory_json, price_modifier FROM shop_events WHERE id = ?",
            (event_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"error": "event not found"}
        shop_id, inventory_json, price_modifier = row
        if inventory_json:
            _apply_inventory(conn, shop_id, json.loads(inventory_json))
        if price_modifier and price_modifier != 1.0:
            conn.execute(
                "UPDATE shop_items SET price_cents = CAST(price_cents * ? AS INTEGER) WHERE shop_id = ?",
                (price_modifier, shop_id),
            )
        conn.execute("UPDATE shop_events SET active = 1 WHERE id = ?", (event_id,))
        conn.commit()
    return {"status": "started"}


def end_shop_event(event_id: int) -> Dict[str, str]:
    """Handler to deactivate a shop event and revert pricing."""

    _ensure_shop_event_schema()
    with _conn() as conn:
        cur = conn.execute(
            "SELECT shop_id, price_modifier FROM shop_events WHERE id = ?",
            (event_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"error": "event not found"}
        shop_id, price_modifier = row
        if price_modifier and price_modifier != 1.0:
            conn.execute(
                "UPDATE shop_items SET price_cents = CAST(price_cents / ? AS INTEGER) WHERE shop_id = ?",
                (price_modifier, shop_id),
            )
        conn.execute("UPDATE shop_events SET active = 0 WHERE id = ?", (event_id,))
        conn.commit()
    return {"status": "ended"}


def get_active_shop_event() -> Dict[str, Any] | None:
    """Return the currently active shop event, if any."""

    _ensure_shop_event_schema()
    with _conn() as conn:
        cur = conn.execute(
            """
            SELECT id, name, banner, end_time
              FROM shop_events
             WHERE active = 1
             ORDER BY start_time DESC
             LIMIT 1
            """
        )
        row = cur.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "name": row[1],
        "banner": row[2],
        "end_time": row[3],
    }


def list_shop_events() -> List[Dict[str, Any]]:
    """List all scheduled shop events."""

    _ensure_shop_event_schema()
    with _conn() as conn:
        cur = conn.execute(
            """
            SELECT id, name, banner, shop_id, start_time, end_time,
                   inventory_json, price_modifier, active
              FROM shop_events
             ORDER BY start_time
            """
        )
        rows = cur.fetchall()
    events: List[Dict[str, Any]] = []
    for r in rows:
        events.append(
            {
                "id": r[0],
                "name": r[1],
                "banner": r[2],
                "shop_id": r[3],
                "start_time": r[4],
                "end_time": r[5],
                "inventory": json.loads(r[6] or "{}"),
                "price_modifier": r[7],
                "active": bool(r[8]),
            }
        )
    return events


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

# ---------------------------------------------------------------------------
# Elite events
# ---------------------------------------------------------------------------

def schedule_elite_event(user_id: int, event: Dict[str, Any]) -> Dict[str, Any]:
    """Register an elite event if the user meets the reputation threshold."""

    if reputation_service.get_reputation(user_id) < ELITE_REPUTATION_THRESHOLD:
        raise PermissionError("Insufficient reputation for elite events")
    return event
