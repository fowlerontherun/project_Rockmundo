import sqlite3
from backend import database

def setup_db(tmp_path):
    db_file = tmp_path / "daily_loop.db"
    database.DB_PATH = db_file
    database.init_db()
    from backend.models import daily_loop as dl_model
    dl_model.DB_PATH = db_file
    return dl_model

def test_weekly_milestone_rollover(tmp_path):
    dl = setup_db(tmp_path)
    with sqlite3.connect(database.DB_PATH) as conn:
        conn.execute(
            "INSERT INTO daily_loop (user_id, weekly_goal_count, tier_progress) VALUES (1,5,3)"
        )
        conn.commit()
    dl.reset_weekly_milestones(1)
    with sqlite3.connect(database.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT weekly_goal_count, tier_progress FROM daily_loop WHERE user_id=1"
        )
        row = cur.fetchone()
        assert row == (0, 0)

def test_reward_progression_advances_tier(tmp_path):
    dl = setup_db(tmp_path)
    with sqlite3.connect(database.DB_PATH) as conn:
        conn.execute(
            "INSERT INTO daily_loop (user_id, challenge_tier, tier_progress, reward_claimed) VALUES (1,1,2,1)"
        )
        conn.commit()
    dl.advance_tier(1)
    with sqlite3.connect(database.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT challenge_tier, tier_progress, reward_claimed FROM daily_loop WHERE user_id=1"
        )
        row = cur.fetchone()
        assert row == (2, 0, 0)
