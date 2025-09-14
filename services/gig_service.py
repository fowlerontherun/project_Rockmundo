import sqlite3
import random
from datetime import datetime, timedelta

from backend.database import DB_PATH
from backend.services import fan_service
from backend.services.skill_service import skill_service
from models.skill import Skill
from models.learning_method import LearningMethod
from backend.services.economy_service import EconomyService


try:  # pragma: no cover - optional in minimal environments
    from services.band_service import BandService
except Exception:  # pragma: no cover
    class BandService:  # type: ignore
        def get_band_info(self, _band_id: int):
            return None

        def increment_fame(self, _band_id: int, _amount: int) -> None:
            return None

try:  # pragma: no cover - optional avatar dependency
    from services.avatar_service import AvatarService
    from backend.schemas.avatar import AvatarUpdate
except Exception:  # pragma: no cover
    class AvatarUpdate:  # type: ignore
        def __init__(self, **kwargs):
            pass

    class AvatarService:  # type: ignore
        def get_avatar(self, _user_id: int):
            return None

        def update_avatar(self, *_args, **_kwargs):
            return None

from seeds.skill_seed import SKILL_NAME_TO_ID

avatar_service = AvatarService()
band_service = BandService()
economy_service = EconomyService()
economy_service.ensure_schema()


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

    # === Skill-based performance multiplier ===
    perf_skill = Skill(
        id=SKILL_NAME_TO_ID["performance"], name="performance", category="stage"
    )
    member_rows: list[tuple[int, str]] = []
    try:
        cur.execute(
            "SELECT user_id, role FROM band_members WHERE band_id = ?", (band_id,)
        )
        member_rows = cur.fetchall()
    except sqlite3.Error:
        member_rows = []
    skill_avgs: list[float] = []
    for uid, role in member_rows:
        perf_level = skill_service.train(uid, perf_skill, 0).level
        inst_level = 0
        if role and role in SKILL_NAME_TO_ID:
            inst_skill = Skill(
                id=SKILL_NAME_TO_ID[role], name=role, category="instrument"
            )
            inst_level = skill_service.train(uid, inst_skill, 0).level
        skill_avgs.append((perf_level + inst_level) / 2)
    avg_skill = sum(skill_avgs) / len(skill_avgs) if skill_avgs else 0
    perf_mult = 1 + avg_skill / 100

    # === Estimate attendance ===
    fan_stats = fan_service.get_band_fan_stats(band_id)
    base_attendance = int(
        fan_stats["total_fans"] * (fan_stats["average_loyalty"] / 100)
    )
    randomness = random.randint(-10, 10)

    band_info = band_service.get_band_info(band_id)
    founder_id = band_info["founder_id"] if band_info else band_id
    try:
        avatar = avatar_service.get_avatar(founder_id)
    except Exception:  # pragma: no cover - fallback if avatar tables missing
        avatar = None
    voice_val = getattr(avatar, "voice", 50)
    stage_presence = getattr(avatar, "stage_presence", 50)

    attendance = max(
        0,
        min(
            venue_size,
            int(
                (base_attendance + randomness)
                * (1 + voice_val / 200)
                * (1 + stage_presence / 500)
                * perf_mult
            ),
        ),
    )

    # Scale outcomes by performance-related skills
    mult = skill_service.get_category_multiplier(band_id, "performance")
    attendance = max(0, min(venue_size, int(attendance * mult)))

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

    economy_service.record_gig_payout(band_id, earnings)
    if hasattr(band_service, "increment_fame"):
        band_service.increment_fame(band_id, fame_gain)
    if avatar and hasattr(avatar_service, "update_avatar"):
        new_fatigue = min(
            100, getattr(avatar, "fatigue", 0) + max(1, venue_size // 100)
        )
        try:
            avatar_service.update_avatar(avatar.id, AvatarUpdate(fatigue=new_fatigue))
        except Exception:  # pragma: no cover - ignore if update fails
            pass

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
        "status": "completed",
    }
