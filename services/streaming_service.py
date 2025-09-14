# File: backend/services/streaming_service.py
from datetime import datetime, timezone

try:  # pragma: no cover - prefer local stub if available
    import utils.aiosqlite_local as aiosqlite
except ModuleNotFoundError:  # pragma: no cover - fallback to package
    import aiosqlite  # type: ignore
from backend.database import DB_PATH
from backend.models.skill import Skill
from backend.seeds.skill_seed import SKILL_NAME_TO_ID
from services.skill_service import skill_service
from services.song_popularity_service import add_event


async def _stream_song(user_id: int, song_id: int) -> dict:
    conn = await aiosqlite.connect(DB_PATH)
    try:
        await conn.execute(
            """
            INSERT INTO streams (user_id, song_id, timestamp)
            VALUES (?, ?, ?)
            """,
            (user_id, song_id, datetime.now(timezone.utc)),
        )
        await conn.execute(
            """
            UPDATE songs
            SET play_count = play_count + 1
            WHERE id = ?
            """,
            (song_id,),
        )
        revenue = 0.003
        cur = await conn.execute(
            "SELECT user_id, percent FROM royalties WHERE song_id = ?",
            (song_id,),
        )
        royalty_rows = await cur.fetchall()
        for receiver_id, percent in royalty_rows:
            amount = revenue * (percent / 100)
            await conn.execute(
                """
                INSERT INTO earnings (user_id, source_type, source_id, amount, timestamp)
                VALUES (?, 'stream', ?, ?, ?)
                """,
                (
                    receiver_id,
                    song_id,
                    amount,
                    datetime.now(timezone.utc),
                ),
            )
        await conn.commit()
    finally:
        await conn.close()
    add_event(song_id, 1.0, "stream")
    return {"status": "ok", "revenue": round(revenue, 4)}


async def stream_song(user_id: int, song_id: int) -> dict:
    """Asynchronously record a song stream."""

    return await _stream_song(user_id, song_id)


async def get_stream_count(song_id: int) -> int:
    conn = await aiosqlite.connect(DB_PATH)
    try:
        cur = await conn.execute(
            "SELECT COUNT(*) FROM streams WHERE song_id = ?",
            (song_id,),
        )
        row = await cur.fetchone()
        return int(row[0]) if row else 0
    finally:
        await conn.close()


async def calculate_stream_revenue(song_id: int) -> float:
    total_streams = await get_stream_count(song_id)
    return round(total_streams * 0.003, 2)


async def list_top_streamed_songs(limit: int = 10) -> list:
    conn = await aiosqlite.connect(DB_PATH)
    try:
        cur = await conn.execute(
            """
            SELECT s.id, s.title, s.play_count, b.name
            FROM songs s
            JOIN bands b ON s.band_id = b.id
            ORDER BY s.play_count DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cur.fetchall()
        return [dict(zip(["song_id", "title", "play_count", "band_name"], row)) for row in rows]
    finally:
        await conn.close()


async def get_user_stream_history(user_id: int) -> list:
    conn = await aiosqlite.connect(DB_PATH)
    try:
        cur = await conn.execute(
            """
            SELECT s.title, str.timestamp
            FROM streams str
            JOIN songs s ON str.song_id = s.id
            WHERE str.user_id = ?
            ORDER BY str.timestamp DESC
            LIMIT 50
            """,
            (user_id,),
        )
        rows = await cur.fetchall()
        return [dict(zip(["song_title", "timestamp"], row)) for row in rows]
    finally:
        await conn.close()


LIVE_STREAMING_SKILL = Skill(
    id=SKILL_NAME_TO_ID["live_streaming"],
    name="live_streaming",
    category="performance",
)


def perform_live_stream(
    user_id: int,
    duration_minutes: int,
    base_viewers: int = 100,
) -> dict:
    """Simulate a live stream and award XP.

    The viewer retention and tips are influenced by the user's
    ``live_streaming`` skill level. Each minute grants one XP.
    """

    skill = skill_service.train(user_id, LIVE_STREAMING_SKILL, duration_minutes)
    retention_rate = min(1.0, 0.4 + 0.02 * skill.level)
    retained = int(base_viewers * retention_rate)
    tips = round(retained * 0.1 * (1 + skill.level / 100), 2)
    return {
        "retained_viewers": retained,
        "tips": tips,
        "skill_level": skill.level,
    }
