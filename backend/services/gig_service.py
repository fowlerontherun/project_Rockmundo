import sqlite3
import random
from datetime import datetime, timedelta

from backend.database import DB_PATH
from backend.services import fan_service
from backend.services.skill_service import skill_service
from backend.models.skill import Skill
from backend.models.learning_method import LearningMethod
from seeds.skill_seed import SKILL_NAME_TO_ID


def create_gig(band_id: int, city: str, venue_size: int, date: str, ticket_price: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO gigs (band_id, city, venue_size, date, ticket_price, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (band_id, city, venue_size, date, ticket_price, "scheduled"))

    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Gig scheduled"}


def cancel_gig(gig_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("UPDATE gigs SET status = ? WHERE id = ?", ("cancelled", gig_id))
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Gig cancelled"}


def get_band_gigs(band_id: int) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, city, venue_size, date, ticket_price, status
        FROM gigs
        WHERE band_id = ?
        ORDER BY date
    """, (band_id,))
    gigs = cur.fetchall()

    conn.close()
    return [dict(zip(["id", "city", "venue_size", "date", "ticket_price", "status"], g)) for g in gigs]


def simulate_gig_result(gig_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT band_id, city, venue_size, ticket_price
        FROM gigs
        WHERE id = ?
    """, (gig_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return {"error": "Gig not found"}

    band_id, city, venue_size, ticket_price = row

    # === Estimate attendance ===
    fan_stats = fan_service.get_band_fan_stats(band_id)
    base_attendance = int(fan_stats["total_fans"] * (fan_stats["average_loyalty"] / 100))
    randomness = random.randint(-10, 10)
    attendance = max(0, min(venue_size, base_attendance + randomness))

    # === Calculate earnings and fame ===
    earnings = attendance * ticket_price
    fame_gain = attendance // 20

    # === Update gig record ===
    cur.execute("""
        UPDATE gigs
        SET attendance = ?, revenue = ?, fame_gain = ?, status = ?
        WHERE id = ?
    """, (attendance, earnings, fame_gain, "completed", gig_id))

    conn.commit()
    conn.close()

    # Boost fans after gig
    fan_service.boost_fans_after_gig(band_id, city, attendance)

    # Practice boosts performance skill scaled by venue size
    performance_skill = Skill(
        id=SKILL_NAME_TO_ID["performance"], name="performance", category="stage"
    )
    difficulty = max(1, venue_size // 50)
    skill_service.train_with_method(
        band_id, performance_skill, LearningMethod.PRACTICE, difficulty
    )

    return {
        "attendance": attendance,
        "earnings": earnings,
        "fame_gain": fame_gain,
        "city": city,
        "status": "completed"
    }