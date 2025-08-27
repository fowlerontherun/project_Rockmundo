import utils.db as db_utils
from utils.db import get_conn
from services.fan_insight_service import FanInsightService

DDL = """
CREATE TABLE users(id INTEGER PRIMARY KEY, age INTEGER, region TEXT);
CREATE TABLE events(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, created_at TEXT);
CREATE TABLE purchases(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount_cents INTEGER, created_at TEXT);
CREATE TABLE streams(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, created_at TEXT);
"""


def setup_db(path: str) -> None:
    with get_conn(path) as conn:
        conn.executescript(DDL)
        conn.executemany(
            "INSERT INTO users(id,age,region) VALUES (?,?,?)",
            [(1, 17, "NA"), (2, 25, "EU"), (3, 40, "NA"), (4, 30, "AS")],
        )
        conn.executemany(
            "INSERT INTO events(user_id,created_at) VALUES (?,?)",
            [
                (1, "2024-01-01"),
                (2, "2024-01-02"),
                (3, "2024-01-02"),
                (4, "2024-01-02"),
            ],
        )
        conn.executemany(
            "INSERT INTO purchases(user_id,amount_cents,created_at) VALUES (?,?,?)",
            [
                (1, 500, "2024-01-01"),
                (2, 1500, "2024-01-01"),
                (2, 1000, "2024-01-02"),
                (3, 6000, "2024-01-02"),
            ],
        )
        conn.executemany(
            "INSERT INTO streams(user_id,created_at) VALUES (?,?)",
            [(1, "2024-01-01"), (1, "2024-01-02"), (2, "2024-01-02")],
        )


def test_segments_and_trends(tmp_path):
    db = str(tmp_path / "fans.db")
    setup_db(db)
    db_utils.DEFAULT_DB = db
    svc = FanInsightService(db_path=db)

    summary = svc.segment_summary()
    assert {b.bucket: b.fans for b in summary.age} == {
        "<18": 1,
        "25-34": 2,
        "35+": 1,
    }
    assert {b.region: b.fans for b in summary.region} == {
        "AS": 1,
        "EU": 1,
        "NA": 2,
    }
    assert {b.bucket: b.fans for b in summary.spend} == {
        "high": 1,
        "low": 2,
        "mid": 1,
    }

    trends = svc.trends("2024-01-01", "2024-01-02")
    assert [m.dict() for m in trends.events] == [
        {"date": "2024-01-01", "value": 1},
        {"date": "2024-01-02", "value": 3},
    ]
    assert [m.dict() for m in trends.purchases] == [
        {"date": "2024-01-01", "value": 2000},
        {"date": "2024-01-02", "value": 7000},
    ]
    assert [m.dict() for m in trends.streams] == [
        {"date": "2024-01-01", "value": 1},
        {"date": "2024-01-02", "value": 2},
    ]
