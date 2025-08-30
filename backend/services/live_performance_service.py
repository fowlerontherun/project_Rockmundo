import sqlite3
import random
from datetime import datetime
from backend.database import DB_PATH
from backend.services.city_service import city_service


def simulate_gig(band_id: int, city: str, venue: str, setlist: list) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

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

    fame_earned = crowd_size // 10
    revenue_earned = crowd_size * 5
    skill_gain = len(setlist) * 0.3
    merch_sold = int(crowd_size * 0.15 * city_service.get_market_demand(city))

    # Record performance
    cur.execute("""
        INSERT INTO live_performances (
            band_id, city, venue, date, setlist,
            crowd_size, fame_earned, revenue_earned,
            skill_gain, merch_sold
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        band_id, city, venue, datetime.utcnow().isoformat(), ",".join(setlist),
        crowd_size, fame_earned, revenue_earned, skill_gain, merch_sold
    ))

    # Update band stats
    cur.execute("UPDATE bands SET fame = fame + ? WHERE id = ?", (fame_earned, band_id))
    cur.execute("UPDATE bands SET skill = skill + ? WHERE id = ?", (skill_gain, band_id))
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
        "skill_gain": skill_gain,
        "merch_sold": merch_sold
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