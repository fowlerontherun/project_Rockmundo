import sqlite3
from datetime import datetime
from backend.database import DB_PATH
from backend.services import fan_service
from backend.services.skill_service import skill_service
from backend.seeds.skill_seed import SEED_SKILLS

FASHION_SKILL = next(s for s in SEED_SKILLS if s.name == "fashion")
IMAGE_MANAGEMENT_SKILL = next(
    s for s in SEED_SKILLS if s.name == "image_management"
)


def _image_bonus(band_id: int) -> int:
    """Calculate fan bonus from a band's image-related skills."""
    fashion = skill_service.train(band_id, FASHION_SKILL, 0)
    management = skill_service.train(band_id, IMAGE_MANAGEMENT_SKILL, 0)
    return (fashion.level + management.level) // 5


def record_interaction(band_id: int, fan_id: int, interaction_type: str, content: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO fan_interactions (band_id, fan_id, interaction_type, content, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (band_id, fan_id, interaction_type, content, datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()

    bonus = _image_bonus(band_id)
    for _ in range(bonus):
        fan_service.add_fan(None, band_id, "online", "image")
    return {
        "status": "ok",
        "message": "Interaction recorded",
        "fans_gained": bonus,
    }


def get_band_interactions(band_id: int, interaction_type: str = None) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if interaction_type:
        cur.execute("""
            SELECT fan_id, interaction_type, content, created_at
            FROM fan_interactions
            WHERE band_id = ? AND interaction_type = ?
            ORDER BY created_at DESC
        """, (band_id, interaction_type))
    else:
        cur.execute("""
            SELECT fan_id, interaction_type, content, created_at
            FROM fan_interactions
            WHERE band_id = ?
            ORDER BY created_at DESC
        """, (band_id,))

    rows = cur.fetchall()
    conn.close()
    return [dict(zip(["fan_id", "interaction_type", "content", "created_at"], row)) for row in rows]


def aggregate_petitions_by_city() -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT content, COUNT(*) as count
        FROM fan_interactions
        WHERE interaction_type = 'petition'
        GROUP BY content
        ORDER BY count DESC
        LIMIT 10
    """)

    rows = cur.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}