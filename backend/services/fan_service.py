import sqlite3

from backend.database import DB_PATH
from backend.models.skill import Skill
from backend.seeds.skill_seed import SKILL_NAME_TO_ID
from backend.services.avatar_service import AvatarService
from backend.services.skill_service import skill_service

avatar_service = AvatarService()


def add_fan(user_id: int, band_id: int, location: str, source: str = "organic") -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    avatar = avatar_service.get_avatar(band_id)
    charisma = avatar.charisma if avatar else 50
    social_media = getattr(avatar, "social_media", 0) if avatar else 0
    loyalty_gain = 10 + charisma // 20 + social_media // 25

    # Check if fan already exists in that location
    cur.execute(
        """
        SELECT id, loyalty FROM fans
        WHERE user_id = ? AND band_id = ? AND location = ?
        """,
        (user_id, band_id, location),
    )
    row = cur.fetchone()

    if row:
        # Increase loyalty if already exists
        fan_id, loyalty = row
        new_loyalty = min(loyalty + loyalty_gain, 100)
        cur.execute(
            "UPDATE fans SET loyalty = ? WHERE id = ?", (new_loyalty, fan_id)
        )
    else:
        # Create new fan record
        base_loyalty = 25 + charisma // 10 + social_media // 10
        cur.execute(
            """
            INSERT INTO fans (user_id, band_id, location, loyalty, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, band_id, location, base_loyalty, source),
        )

    conn.commit()
    conn.close()
    return {"status": "ok", "action": "added_or_updated"}


def decay_fan_loyalty():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Decrease loyalty by 1 for all fans, remove if below threshold
    cur.execute(
        """
        UPDATE fans
        SET loyalty = loyalty - 1
        WHERE loyalty > 0
        """
    )

    cur.execute("DELETE FROM fans WHERE loyalty <= 0")

    conn.commit()
    conn.close()
    return {"status": "ok", "action": "loyalty_decayed"}


def get_band_fan_stats(band_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COUNT(*), AVG(loyalty)
        FROM fans
        WHERE band_id = ?
        """,
        (band_id,),
    )
    count, avg_loyalty = cur.fetchone()

    conn.close()
    return {
        "total_fans": count or 0,
        "average_loyalty": round(avg_loyalty or 0, 2),
    }


def boost_fans_after_gig(band_id: int, location: str, attendance: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    avatar = avatar_service.get_avatar(band_id)
    charisma = avatar.charisma if avatar else 50
    social_media = getattr(avatar, "social_media", 0) if avatar else 0
    charisma_bonus = max(1, (charisma + social_media) // 50)

    # Boost existing fans in that location
    cur.execute(
        """
        UPDATE fans
        SET loyalty = MIN(loyalty + ?, 100)
        WHERE band_id = ? AND location = ?
        """,
        (5 + charisma_bonus, band_id, location),
    )

    # Add new fans based on attendance and marketing/PR/image skill levels
    base_new = attendance // 10
    marketing = Skill(
        id=SKILL_NAME_TO_ID.get("marketing", 0),
        name="marketing",
        category="business",
    )
    pr_skill = Skill(
        id=SKILL_NAME_TO_ID.get("public_relations", 0),
        name="public_relations",
        category="business",
    )
    fashion = Skill(
        id=SKILL_NAME_TO_ID.get("fashion", 0),
        name="fashion",
        category="image",
    )
    image_mgmt = Skill(
        id=SKILL_NAME_TO_ID.get("image_management", 0),
        name="image_management",
        category="image",
    )
    marketing_level = skill_service.train(band_id, marketing, 0).level
    pr_level = skill_service.train(band_id, pr_skill, 0).level
    fashion_level = skill_service.train(band_id, fashion, 0).level
    image_level = skill_service.train(band_id, image_mgmt, 0).level
    skill_multiplier = (
        1
        + 0.05 * max(marketing_level - 1, 0)
        + 0.05 * max(pr_level - 1, 0)
        + 0.05 * max(fashion_level - 1, 0)
        + 0.05 * max(image_level - 1, 0)
    )
    social_multiplier = 1 + social_media / 100
    new_fans = int(base_new * skill_multiplier * social_multiplier)
    for _ in range(new_fans):
        cur.execute(
            """
            INSERT INTO fans (user_id, band_id, location, loyalty, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            (None, band_id, location, 20 + charisma_bonus, "gig"),
        )

    conn.commit()
    conn.close()
    return {"status": "ok", "fans_boosted": new_fans}


__all__ = [
    "add_fan",
    "decay_fan_loyalty",
    "get_band_fan_stats",
    "boost_fans_after_gig",
]
