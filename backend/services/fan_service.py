import sqlite3
from backend.database import DB_PATH
from backend.services.avatar_service import AvatarService

avatar_service = AvatarService()


def add_fan(user_id: int, band_id: int, location: str, source: str = "organic") -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    avatar = avatar_service.get_avatar(band_id)
    charisma = avatar.charisma if avatar else 50
    loyalty_gain = 10 + charisma // 20

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
        base_loyalty = 25 + charisma // 10
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
    cur.execute("""
        UPDATE fans
        SET loyalty = loyalty - 1
        WHERE loyalty > 0
    """)

    cur.execute("DELETE FROM fans WHERE loyalty <= 0")

    conn.commit()
    conn.close()
    return {"status": "ok", "action": "loyalty_decayed"}


def get_band_fan_stats(band_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*), AVG(loyalty)
        FROM fans
        WHERE band_id = ?
    """, (band_id,))
    count, avg_loyalty = cur.fetchone()

    conn.close()
    return {
        "total_fans": count or 0,
        "average_loyalty": round(avg_loyalty or 0, 2)
    }


def boost_fans_after_gig(band_id: int, location: str, attendance: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    avatar = avatar_service.get_avatar(band_id)
    charisma = avatar.charisma if avatar else 50
    bonus = max(1, charisma // 50)

    # Boost existing fans in that location
    cur.execute(
        """
        UPDATE fans
        SET loyalty = MIN(loyalty + ? , 100)
        WHERE band_id = ? AND location = ?
    """,
        (5 + bonus, band_id, location),
    )

    # Add new fans based on attendance
    new_fans = (attendance // 10) * bonus
    for _ in range(new_fans):
        cur.execute(
            """
            INSERT INTO fans (user_id, band_id, location, loyalty, source)
            VALUES (?, ?, ?, ?, ?)
        """,
            (None, band_id, location, 20 + bonus, "gig"),
        )

    conn.commit()
    conn.close()
    return {"status": "ok", "fans_boosted": new_fans}