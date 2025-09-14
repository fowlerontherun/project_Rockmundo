import random
import sqlite3
from datetime import date, timedelta
from typing import Dict, Optional

from backend.database import DB_PATH
from backend.services.xp_reward_service import xp_reward_service
from models import weekly_drop, tier_track

CHALLENGES = [
    "Practice scales",
    "Write a chorus",
    "Listen to a new song",
]

CHALLENGE_TIERS = [1, 2, 3]


def _ensure_row(cur: sqlite3.Cursor, user_id: int) -> None:
    cur.execute(
        """
        INSERT OR IGNORE INTO daily_loop (
            user_id,
            login_streak,
            last_login,
            current_challenge,
            challenge_progress,
            reward_claimed,
            catch_up_tokens,
            challenge_tier,
            weekly_goal_count,
            tier_progress
        )
        VALUES (?, 0, NULL, '', 0, 0, 0, 1, 0, 0)
        """,
        (user_id,),
    )


def get_status(user_id: int) -> Dict:
    """Return current streak, challenge, and reward state for a user."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    _ensure_row(cur, user_id)
    cur.execute(
        """
        SELECT
            login_streak,
            last_login,
            current_challenge,
            challenge_progress,
            reward_claimed,
            catch_up_tokens,
            challenge_tier,
            weekly_goal_count,
            tier_progress
        FROM daily_loop
        WHERE user_id = ?
    """,
        (user_id,),
    )
    row = cur.fetchone()
    next_weekly = weekly_drop.get_next_drop(user_id)
    next_tier_reward = tier_track.get_reward(row[6] + 1)
    conn.close()
    return {
        "login_streak": row[0],
        "last_login": row[1],
        "current_challenge": row[2],
        "challenge_progress": row[3],
        "reward_claimed": bool(row[4]),
        "catch_up_tokens": row[5],
        "challenge_tier": row[6],
        "weekly_goal_count": row[7],
        "tier_progress": row[8],
        "next_weekly_reward": next_weekly,
        "next_tier_reward": next_tier_reward,
    }


def increment_login_streak(user_id: int) -> Dict:
    """Increment the login streak for today."""
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    _ensure_row(cur, user_id)
    cur.execute(
        "SELECT login_streak, last_login FROM daily_loop WHERE user_id = ?",
        (user_id,),
    )
    streak, last_login = cur.fetchone()
    if last_login == today:
        conn.close()
        return get_status(user_id)
    if last_login == (date.today() - date.resolution).isoformat():
        streak += 1
    else:
        streak = 1
    cur.execute(
        "UPDATE daily_loop SET login_streak = ?, last_login = ? WHERE user_id = ?",
        (streak, today, user_id),
    )
    conn.commit()
    conn.close()
    return get_status(user_id)


def claim_reward(user_id: int) -> Dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    _ensure_row(cur, user_id)
    cur.execute("SELECT challenge_tier FROM daily_loop WHERE user_id = ?", (user_id,))
    tier = cur.fetchone()[0]
    cur.execute(
        "UPDATE daily_loop SET reward_claimed = 1 WHERE user_id = ?",
        (user_id,),
    )
    conn.commit()
    conn.close()
    # Award XP based on challenge tier
    xp_reward_service.grant_daily_reward(user_id, tier)
    return get_status(user_id)


def grant_catch_up_tokens(user_id: int, amount: int = 1) -> Dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    _ensure_row(cur, user_id)
    cur.execute(
        "UPDATE daily_loop SET catch_up_tokens = catch_up_tokens + ? WHERE user_id = ?",
        (amount, user_id),
    )
    conn.commit()
    conn.close()
    return get_status(user_id)


def rotate_daily_challenge() -> None:
    challenge = random.choice(CHALLENGES)
    tier = random.choice(CHALLENGE_TIERS)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE daily_loop
        SET current_challenge = ?, challenge_progress = 0, reward_claimed = 0, challenge_tier = ?
    """,
        (challenge, tier),
    )
    next_drop = (date.today() + timedelta(days=7)).isoformat()
    cur.execute("SELECT user_id FROM daily_loop")
    users = [row[0] for row in cur.fetchall()]
    reward = tier_track.get_reward(tier) or "mystery"
    conn.commit()
    conn.close()
    for uid in users:
        weekly_drop.schedule_drop(uid, next_drop, reward)


def reset_weekly_milestones(user_id: int) -> Dict:
    """Reset weekly goal counters and tier progress for a user."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    _ensure_row(cur, user_id)
    cur.execute(
        "UPDATE daily_loop SET weekly_goal_count = 0, tier_progress = 0 WHERE user_id = ?",
        (user_id,),
    )
    conn.commit()
    conn.close()
    return get_status(user_id)


def advance_tier(user_id: int) -> Dict:
    """Advance the user's challenge tier and reset progress."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    _ensure_row(cur, user_id)
    cur.execute(
        """
        UPDATE daily_loop
        SET challenge_tier = challenge_tier + 1,
            tier_progress = 0,
            reward_claimed = 0
        WHERE user_id = ?
        """,
        (user_id,),
    )
    conn.commit()
    conn.close()
    return get_status(user_id)
