import random
import sqlite3
from datetime import date
from typing import Dict

from backend.database import DB_PATH

CHALLENGES = [
    "Practice scales",
    "Write a chorus",
    "Listen to a new song",
]


def _ensure_row(cur: sqlite3.Cursor, user_id: int) -> None:
    cur.execute("""
        INSERT OR IGNORE INTO daily_loop (user_id, login_streak, last_login, current_challenge, challenge_progress, reward_claimed)
        VALUES (?, 0, NULL, '', 0, 0)
    """, (user_id,))


def get_status(user_id: int) -> Dict:
    """Return current streak, challenge, and reward state for a user."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    _ensure_row(cur, user_id)
    cur.execute(
        """
        SELECT login_streak, last_login, current_challenge, challenge_progress, reward_claimed
        FROM daily_loop
        WHERE user_id = ?
    """,
        (user_id,),
    )
    row = cur.fetchone()
    conn.close()
    return {
        "login_streak": row[0],
        "last_login": row[1],
        "current_challenge": row[2],
        "challenge_progress": row[3],
        "reward_claimed": bool(row[4]),
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
    cur.execute(
        "UPDATE daily_loop SET reward_claimed = 1 WHERE user_id = ?",
        (user_id,),
    )
    conn.commit()
    conn.close()
    return get_status(user_id)


def rotate_daily_challenge() -> None:
    challenge = random.choice(CHALLENGES)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE daily_loop
        SET current_challenge = ?, challenge_progress = 0, reward_claimed = 0
    """,
        (challenge,),
    )
    conn.commit()
    conn.close()
