import sqlite3

import pytest

from backend.jobs.world_pulse_jobs import run_daily
from backend.services.season_service import activate_season

DDL = """
PRAGMA foreign_keys = ON;
CREATE TABLE artists (
  id   INTEGER PRIMARY KEY,
  name TEXT NOT NULL
);
CREATE TABLE music_events (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  event_time    TEXT NOT NULL,
  artist_id     INTEGER NOT NULL,
  streams       INTEGER NOT NULL DEFAULT 0,
  sales_digital INTEGER NOT NULL DEFAULT 0,
  sales_vinyl   INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(artist_id) REFERENCES artists(id)
);
CREATE TABLE app_config (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
INSERT OR IGNORE INTO app_config(key, value) VALUES
('world_pulse_weights', '{"streams":1.0,"digital":10.0,"vinyl":15.0}');
INSERT OR REPLACE INTO app_config(key, value) VALUES
('seasonal_events', '{"SummerFest":{"start":"2025-08-24","end":"2025-08-26","multiplier":2.0,"active":false}}');
CREATE TABLE job_metadata (
  job_name   TEXT NOT NULL,
  run_at     TEXT NOT NULL,
  status     TEXT NOT NULL,
  details    TEXT,
  PRIMARY KEY (job_name, run_at)
);
CREATE TABLE world_pulse_metrics (
  date           TEXT NOT NULL,
  artist_id      INTEGER NOT NULL,
  streams        INTEGER NOT NULL DEFAULT 0,
  sales_digital  INTEGER NOT NULL DEFAULT 0,
  sales_vinyl    INTEGER NOT NULL DEFAULT 0,
  score          REAL    NOT NULL DEFAULT 0,
  season         TEXT,
  PRIMARY KEY (date, artist_id)
);
CREATE TABLE world_pulse_rankings (
  date        TEXT    NOT NULL,
  season      TEXT,
  rank        INTEGER NOT NULL,
  artist_id   INTEGER NOT NULL,
  name        TEXT    NOT NULL,
  pct_change  REAL,
  score       REAL    NOT NULL,
  PRIMARY KEY (date, season, rank)
);
"""


@pytest.fixture()
def conn(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(DDL)
    yield conn
    conn.close()


def test_seasonal_multiplier_applied(conn):
    conn.execute("INSERT INTO artists(id, name) VALUES(1, 'Neon Fox')")
    conn.execute(
        "INSERT INTO music_events(event_time, artist_id, streams, sales_digital, sales_vinyl) VALUES(?,?,?,?,?)",
        ("2025-08-25T10:00:00", 1, 1000, 20, 5),
    )
    activate_season(conn, "SummerFest")
    run_daily(target_date="2025-08-25", conn_override=conn)

    metric = conn.execute(
        "SELECT score, season FROM world_pulse_metrics WHERE date='2025-08-25' AND artist_id=1"
    ).fetchone()
    ranking = conn.execute(
        "SELECT score, season FROM world_pulse_rankings WHERE date='2025-08-25'"
    ).fetchone()

    base = 1000 + 20 * 10 + 5 * 15
    expected = base * 2.0
    assert metric["season"] == "SummerFest"
    assert pytest.approx(metric["score"], rel=1e-6) == expected
    assert ranking["season"] == "SummerFest"
    assert pytest.approx(ranking["score"], rel=1e-6) == expected
