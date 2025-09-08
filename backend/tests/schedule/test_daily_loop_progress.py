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


def test_weekly_drop_and_next_reward(tmp_path):
    dl = setup_db(tmp_path)
    with sqlite3.connect(database.DB_PATH) as conn:
        conn.executemany(
            "INSERT INTO tier_tracks (tier, reward) VALUES (?, ?)",
            [(1, "bronze"), (2, "silver"), (3, "gold"), (4, "platinum")],
        )
        conn.execute("INSERT INTO daily_loop (user_id) VALUES (1)")
        conn.commit()
    dl.rotate_daily_challenge()
    status = dl.get_status(1)
    assert status["next_weekly_reward"] is not None
    tier = status["challenge_tier"]
    with sqlite3.connect(database.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT reward FROM tier_tracks WHERE tier=?", (tier + 1,))
        expected = cur.fetchone()[0]
    assert status["next_tier_reward"] == expected
    with sqlite3.connect(database.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM weekly_drops WHERE user_id=1")
        assert cur.fetchone()[0] == 1
