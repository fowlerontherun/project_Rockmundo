import json
import random
import sqlite3
from datetime import datetime
from typing import Dict, Generator, Iterable, Optional

from seeds.skill_seed import SKILL_NAME_TO_ID

from backend.database import DB_PATH
from backend.services import live_performance_analysis
from backend.services.chemistry_service import ChemistryService
from backend.services.city_service import city_service
from backend.services.event_service import is_skill_blocked
from backend.services.gear_service import gear_service
from backend.services.setlist_service import get_approved_setlist

try:
    from backend.realtime.polling import poll_hub
except Exception:  # pragma: no cover - optional realtime module
    poll_hub = None  # type: ignore


chemistry_service = ChemistryService()

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
    setlist_or_revision,
    reaction_stream: Optional[Iterable[Dict[str, float]] | Iterable[float]] = None,
    partner_band_ids: Optional[list[int]] = None,
    revenue_split: Optional[Dict[int, float]] = None,
) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if isinstance(setlist_or_revision, int):
        approved = get_approved_setlist(setlist_or_revision)
        if not approved:
            conn.close()
            return {"error": "Setlist revision must be approved"}
        setlist = approved
    else:
        setlist = setlist_or_revision

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

    all_band_ids = [band_id] + (partner_band_ids or [])
    placeholders = ",".join("?" for _ in all_band_ids)
    cur.execute(f"SELECT id, fame FROM bands WHERE id IN ({placeholders})", all_band_ids)
    rows = cur.fetchall()
    if len(rows) != len(all_band_ids):
        conn.close()
        return {"error": "Band not found"}
    fame_map = {r[0]: r[1] for r in rows}

    participant_users: list[int] = []
    try:
        cur.execute(
            f"SELECT band_id, user_id FROM band_members WHERE band_id IN ({placeholders})",
            all_band_ids,
        )
        participant_users = [u for _, u in cur.fetchall()]
    except Exception:
        participant_users = []

    scores = []
    for i, a in enumerate(participant_users):
        for b in participant_users[i + 1 :]:
            pair = chemistry_service.initialize_pair(a, b)
            scores.append(pair.score)
    avg_chem = sum(scores) / len(scores) if scores else 50.0
    chem_mod = 1 + (avg_chem - 50.0) / 100.0

    # Simulate crowd size based on combined fame and randomness
    base_crowd = sum(fame_map.values()) * 2
    crowd_size = min(random.randint(base_crowd, base_crowd + 300), 2000)
    crowd_size = int(crowd_size * city_service.get_event_modifier(city))

    fame_bonus = 0.0
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

    poll_results: Dict[str, int] = {}

    def _handle_action(action: dict) -> None:
        nonlocal skill_gain, fame_bonus
        a_type = action.get("type")
        action_bonus = 0
        fame_modifier = 0
        if a_type == "song" or a_type == "encore":
            skill_gain += 0.3 * chem_mod

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
                        increment = 2 if owner_band in all_band_ids else 1
                        if owner_band not in all_band_ids:
                            song_bonus = 1
                        cur.execute(
                            "UPDATE songs SET play_count = play_count + ? WHERE id = ?",
                            (increment, song_id),
                        )

            action_bonus += song_bonus
        elif a_type == "activity":
            skill_gain += 0.1 * chem_mod
            action_bonus += 1
        if action.get("encore") or a_type == "encore":
            action_bonus += 3

        fame_modifier = 0
        if recent_reactions:
            avg_recent = sum(recent_reactions[-3:]) / len(recent_reactions[-3:])
            if avg_recent > 0.7:
                fame_modifier = 1
            elif avg_recent < 0.3:
                fame_modifier = -1

        fame_bonus += (action_bonus + fame_modifier) * chem_mod

        reaction = next(stream)
        if isinstance(reaction, dict):
            cheers = reaction.get("cheers", 0)
            energy = reaction.get("energy", 0)
        else:
            cheers = energy = float(reaction)
        score = (cheers + energy) / 2 * chem_mod
        score = max(0.0, min(1.0, score))
        recent_reactions.append(score)
        event_log.append(
            {
                "action": a_type,
                "cheers": cheers,
                "energy": energy,
                "crowd_reaction": score,
                "fame_modifier": fame_modifier,
            }
        )

    for action in main_actions:
        _handle_action(action)

    # Pause for encore poll
    if poll_hub is not None:
        poll_id = str(band_id)
        poll_results = poll_hub.results(poll_id)
        poll_hub.clear(poll_id)
        if poll_results:
            sorted_items = sorted(poll_results.items(), key=lambda kv: kv[1], reverse=True)
            top_votes = sorted_items[0][1]
            winners = [song for song, votes in sorted_items if votes == top_votes]
            for song_id in reversed(winners):
                encore_actions.insert(0, {"type": "encore", "reference": str(song_id)})

    for action in encore_actions:
        _handle_action(action)

    fame_total = crowd_size // 10 + fame_bonus
    revenue_total = crowd_size * 5
    skill_gain += gear_service.get_band_bonus(band_id, "performance") * chem_mod
    performance_id = SKILL_NAME_TO_ID["performance"]
    applied_skill = 0 if is_skill_blocked(band_id, performance_id) else skill_gain
    merch_total = int(crowd_size * 0.15 * city_service.get_market_demand(city))

    participants = all_band_ids
    if revenue_split:
        share_map = {int(k): v for k, v in revenue_split.items()}
        missing = [b for b in participants if b not in share_map]
        leftover = (1.0 - sum(share_map.values())) / (len(missing) or 1)
        for b in missing:
            share_map[b] = leftover
    else:
        share_map = {b: 1 / len(participants) for b in participants}

    fame_dist = {b: int(fame_total * share_map[b]) for b in participants}
    revenue_dist = {b: int(revenue_total * share_map[b]) for b in participants}
    skill_dist = {b: applied_skill * share_map[b] for b in participants}
    merch_dist = {b: int(merch_total * share_map[b]) for b in participants}

    # Record performance for each band
    performance_record_id = None
    for b in participants:
        cur.execute(
            """
            INSERT INTO live_performances (
                band_id, city, venue, date, setlist,
                crowd_size, fame_earned, revenue_earned,
                skill_gain, merch_sold
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                b,
                city,
                venue,
                datetime.utcnow().isoformat(),
                json.dumps({"setlist": main_actions, "encore": encore_actions}),
                crowd_size,
                fame_dist[b],
                revenue_dist[b],
                skill_dist[b],
                merch_dist[b],
            ),
        )
        if b == band_id:
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

    if poll_results:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS encore_poll_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                performance_id INTEGER,
                song_id INTEGER,
                votes INTEGER,
                created_at TEXT
            )
            """
        )
        for song_id, votes in poll_results.items():
            cur.execute(
                """
                INSERT INTO encore_poll_results (performance_id, song_id, votes, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    performance_record_id,
                    int(song_id),
                    votes,
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
    for b in participants:
        cur.execute("UPDATE bands SET fame = fame + ? WHERE id = ?", (fame_dist[b], b))
        if skill_dist[b]:
            cur.execute(
                "UPDATE bands SET skill = skill + ? WHERE id = ?",
                (skill_dist[b], b),
            )
        cur.execute(
            "UPDATE bands SET revenue = revenue + ? WHERE id = ?",
            (revenue_dist[b], b),
        )

    conn.commit()
    conn.close()

    for i, a in enumerate(participant_users):
        for b in participant_users[i + 1 :]:
            chemistry_service.adjust_pair(a, b, 1)

    result = {
        "status": "ok",
        "city": city,
        "venue": venue,
        "crowd_size": crowd_size,
        "fame_earned": fame_dist[band_id],
        "revenue_earned": revenue_dist[band_id],
        "skill_gain": skill_dist[band_id],
        "merch_sold": merch_dist[band_id],
        "chemistry_avg": avg_chem,
    }
    if len(participants) > 1:
        result["band_results"] = {
            str(b): {
                "fame_earned": fame_dist[b],
                "revenue_earned": revenue_dist[b],
                "skill_gain": skill_dist[b],
                "merch_sold": merch_dist[b],
            }
            for b in participants
        }
    return result


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
