import random
import sqlite3
import json
from datetime import datetime

from typing import Generator, Iterable, Optional, Dict

from seeds.skill_seed import SKILL_NAME_TO_ID

from backend.database import DB_PATH
from backend.services.city_service import city_service
from backend.services.event_service import is_skill_blocked
from backend.services.gear_service import gear_service
from backend.services.setlist_service import get_approved_setlist
from backend.services import live_performance_analysis

def crowd_reaction_stream() -> Generator[Dict[str, float], None, None]:
    """Endless stream of crowd reaction metrics.

    Each yielded dictionary contains a ``cheers`` and ``energy`` value,
    both normalised between 0 and 1. The function is deterministic enough
    to be swapped out in tests by passing a custom ``reaction_stream`` to
    :func:`simulate_gig`.
    """
    while True:
        yield {
            "cheers": random.uniform(0.0, 1.0),
            "energy": random.uniform(0.0, 1.0),
        }


def simulate_gig(
    band_id: int,
    city: str,
    venue: str,
    setlist_revision_id: int,
    reaction_stream: Optional[Iterable[float]] = None,
    setlist,
    reaction_stream: Optional[Iterable[Dict[str, float]]] = None,
) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    approved = get_approved_setlist(setlist_revision_id)
    if not approved:
        conn.close()
        return {"error": "Setlist revision must be approved"}
    setlist = approved
    # ensure performance_events table exists
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS performance_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            performance_id INTEGER,
            action TEXT,
            crowd_reaction REAL,
            fame_modifier INTEGER,
            created_at TEXT
        )
        """
    )

    # Get band fame
    cur.execute("SELECT fame FROM bands WHERE id = ?", (band_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return {"error": "Band not found"}
    fame = row[0]

    # Simulate crowd size based on fame and randomness
    base_crowd = fame * 2
    crowd_size = min(random.randint(base_crowd, base_crowd + 300), 2000)
    crowd_size = int(crowd_size * city_service.get_event_modifier(city))

    fame_bonus = 0
    skill_gain = 0.0
    event_log = []
    recent_reactions: list[float] = []

    stream = iter(reaction_stream) if reaction_stream is not None else crowd_reaction_stream()

    main_actions: list = []
    encore_actions: list = []
    if isinstance(setlist, dict):
        main_actions = setlist.get("main") or setlist.get("setlist", [])
        encore_actions = setlist.get("encore", [])
    else:
        for action in setlist:
            if action.get("encore") or action.get("type") == "encore":
                encore_actions.append(action)
            else:
                main_actions.append(action)

    for action in main_actions + encore_actions:
        a_type = action.get("type")
        action_bonus = 0
        fame_modifier = 0
        if a_type == "song" or a_type == "encore":
            skill_gain += 0.3

            song_bonus = 2
            ref = action.get("reference")
            if ref is not None:
                ref_str = str(ref)
                if ref_str.isdigit():
                    song_id = int(ref_str)
                    cur.execute("SELECT band_id FROM songs WHERE id = ?", (song_id,))
                    row = cur.fetchone()
                    if row:
                        owner_band = row[0]
                        if owner_band != band_id:
                            song_bonus = 1
                        cur.execute(
                            "UPDATE songs SET play_count = play_count + ? WHERE id = ?",
                            (2 if owner_band == band_id else 1, song_id),
                        )

            action_bonus += song_bonus
        elif a_type == "activity":
            skill_gain += 0.1
            action_bonus += 1
        if action.get("encore") or a_type == "encore":
            action_bonus += 3

        if recent_reactions:
            avg_recent = sum(recent_reactions[-3:]) / len(recent_reactions[-3:])
            if avg_recent > 0.7:
                fame_modifier = 1
            elif avg_recent < 0.3:
                fame_modifier = -1

        fame_bonus += action_bonus + fame_modifier

        reaction = next(stream)
        score = (reaction.get("cheers", 0) + reaction.get("energy", 0)) / 2
        recent_reactions.append(score)
        event_log.append(
            {
                "action": a_type,
                "cheers": reaction.get("cheers", 0),
                "energy": reaction.get("energy", 0),
                "crowd_reaction": score,
                "fame_modifier": fame_modifier,
            }
        )

    fame_earned = crowd_size // 10 + fame_bonus
    revenue_earned = crowd_size * 5
    skill_gain += gear_service.get_band_bonus(band_id, "performance")
    performance_id = SKILL_NAME_TO_ID["performance"]
    applied_skill = 0 if is_skill_blocked(band_id, performance_id) else skill_gain
    merch_sold = int(crowd_size * 0.15 * city_service.get_market_demand(city))

    # Record performance
    cur.execute(
        """
        INSERT INTO live_performances (
            band_id, city, venue, date, setlist,
            crowd_size, fame_earned, revenue_earned,
            skill_gain, merch_sold
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            band_id,
            city,
            venue,
            datetime.utcnow().isoformat(),
            json.dumps({"setlist": main_actions, "encore": encore_actions}),
            crowd_size,
            fame_earned,
            revenue_earned,
            applied_skill,
            merch_sold,
        ),
    )
    performance_record_id = cur.lastrowid

    for event in event_log:
        cur.execute(
            """
            INSERT INTO performance_events (
                performance_id, action, crowd_reaction, fame_modifier, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                performance_record_id,
                event["action"],
                event["crowd_reaction"],
                event["fame_modifier"],
                datetime.utcnow().isoformat(),
            ),
        )

    conn.commit()

    summary = {
        "performance_id": performance_record_id,
        "actions": event_log,
        "average_reaction": sum(r["crowd_reaction"] for r in event_log) / len(event_log)
        if event_log
        else 0,
    }
    live_performance_analysis.store_setlist_summary(summary)

    # Update band stats
    cur.execute("UPDATE bands SET fame = fame + ? WHERE id = ?", (fame_earned, band_id))
    if applied_skill:
        cur.execute("UPDATE bands SET skill = skill + ? WHERE id = ?", (applied_skill, band_id))
    cur.execute("UPDATE bands SET revenue = revenue + ? WHERE id = ?", (revenue_earned, band_id))

    conn.commit()
    conn.close()

    return {
        "status": "ok",
        "city": city,
        "venue": venue,
        "crowd_size": crowd_size,
        "fame_earned": fame_earned,
        "revenue_earned": revenue_earned,
        "skill_gain": applied_skill,
        "merch_sold": merch_sold,
    }


def get_band_performances(band_id: int) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT city, venue, date, setlist, crowd_size, fame_earned, revenue_earned
        FROM live_performances
        WHERE band_id = ?
        ORDER BY date DESC
        LIMIT 50
    """, (band_id,))
    rows = cur.fetchall()
    conn.close()

    return [
        dict(zip([
            "city", "venue", "date", "setlist", "crowd_size",
            "fame_earned", "revenue_earned"
        ], row))
        for row in rows
    ]
