# backend/tests/test_world_pulse_jobs.py
# Pytest: seeds music_events and asserts rankings & pct_change.

import sqlite3

import pytest

from jobs.world_pulse_jobs import run_daily, run_weekly

DDL = """
PRAGMA foreign_keys = ON;

-- Minimal tables for test
CREATE TABLE artists (
  id   INTEGER PRIMARY KEY,
  name TEXT NOT NULL
);

CREATE TABLE music_events (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  event_time    TEXT NOT NULL,    -- ISO timestamp or date
  artist_id     INTEGER NOT NULL,
  streams       INTEGER NOT NULL DEFAULT 0,
  sales_digital INTEGER NOT NULL DEFAULT 0,
  sales_vinyl   INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(artist_id) REFERENCES artists(id)
);

-- Migrations under test (trimmed to essentials)
CREATE TABLE IF NOT EXISTS job_metadata (
  job_name   TEXT NOT NULL,
  run_at     TEXT NOT NULL,
  status     TEXT NOT NULL,
  details    TEXT,
  PRIMARY KEY (job_name, run_at)
);

CREATE TABLE IF NOT EXISTS app_config (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

INSERT OR IGNORE INTO app_config(key, value) VALUES
('world_pulse_weights', '{"streams":1.0,"digital":10.0,"vinyl":15.0}');

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

CREATE TABLE world_pulse_weekly_cache (
  week_start  TEXT    NOT NULL,
  rank        INTEGER NOT NULL,
  artist_id   INTEGER NOT NULL,
  name        TEXT    NOT NULL,
  pct_change  REAL,
  score       REAL    NOT NULL,
  PRIMARY KEY (week_start, rank)
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


def _seed(conn):
    # Two artists
    conn.execute("INSERT INTO artists(id, name) VALUES(1,'Neon Fox')")
    conn.execute("INSERT INTO artists(id, name) VALUES(2,'Velvet Echo')")
    # Day 1: 2025-08-24
    conn.executemany(
        "INSERT INTO music_events(event_time, artist_id, streams, sales_digital, sales_vinyl) VALUES(?,?,?,?,?)",
        [
            ("2025-08-24T10:00:00", 1, 1000, 20, 5),  # Neon Fox
            ("2025-08-24T12:00:00", 2,  800, 30, 2),  # Velvet Echo
        ],
    )
    # Day 2: 2025-08-25
    conn.executemany(
        "INSERT INTO music_events(event_time, artist_id, streams, sales_digital, sales_vinyl) VALUES(?,?,?,?,?)",
        [
            ("2025-08-25T09:00:00", 1, 900,  25, 4),  # Neon Fox (slight down on streams, up on sales_digital)
            ("2025-08-25T09:15:00", 2, 1200, 15, 1),  # Velvet Echo (big stream spike, lower sales)
        ],
    )
    conn.commit()


def test_daily_rankings_and_pct_change(conn, monkeypatch):
    _seed(conn)

    # Monkeypatch the jobs to use our test connection
    # Day 1 (baseline)
    run_daily(target_date="2025-08-24", conn_override=conn)
    rows = conn.execute(
        "SELECT * FROM world_pulse_rankings WHERE date = '2025-08-24' ORDER BY rank"
    ).fetchall()
    assert len(rows) == 2

    # With default weights: score = streams*1 + digital*10 + vinyl*15
    # 2025-08-24:
    # Neon Fox: 1000 + 20*10 + 5*15 = 1000 + 200 + 75 = 1275
    # Velvet Echo: 800 + 30*10 + 2*15 = 800 + 300 + 30 = 1130
    assert rows[0]["name"] == "Neon Fox"
    assert pytest.approx(rows[0]["score"], rel=1e-6) == 1275.0
    assert rows[0]["pct_change"] is None  # No previous day

    assert rows[1]["name"] == "Velvet Echo"
    assert pytest.approx(rows[1]["score"], rel=1e-6) == 1130.0
    assert rows[1]["pct_change"] is None

    # Day 2
    run_daily(target_date="2025-08-25", conn_override=conn)
    rows2 = conn.execute(
        "SELECT * FROM world_pulse_rankings WHERE date = '2025-08-25' ORDER BY rank"
    ).fetchall()
    assert len(rows2) == 2

    # 2025-08-25:
    # Neon Fox: 900 + 25*10 + 4*15 = 900 + 250 + 60 = 1210
    # Velvet Echo: 1200 + 15*10 + 1*15 = 1200 + 150 + 15 = 1365
    # Rankings flip: Velvet Echo now #1
    assert rows2[0]["name"] == "Velvet Echo"
    assert pytest.approx(rows2[0]["score"], rel=1e-6) == 1365.0
    # pct_change for Velvet Echo vs prev day (1130): (1365-1130)/1130 = ~0.20885
    assert pytest.approx(rows2[0]["pct_change"], rel=1e-6) == (1365.0 - 1130.0) / 1130.0

    assert rows2[1]["name"] == "Neon Fox"
    assert pytest.approx(rows2[1]["score"], rel=1e-6) == 1210.0
    # pct_change for Neon Fox vs prev day (1275): (1210-1275)/1275 = ~-0.05098
    assert pytest.approx(rows2[1]["pct_change"], rel=1e-6) == (1210.0 - 1275.0) / 1275.0


def test_weekly_cache_rollup(conn):
    _seed(conn)
    # Build daily first for both days
    run_daily(target_date="2025-08-24", conn_override=conn)
    run_daily(target_date="2025-08-25", conn_override=conn)

    # Monday of week including 2025-08-25 is 2025-08-25
    run_weekly(week_start="2025-08-25", conn_override=conn)

    weekly = conn.execute(
        "SELECT * FROM world_pulse_weekly_cache WHERE week_start='2025-08-25' ORDER BY rank"
    ).fetchall()
    assert len(weekly) == 2

    # Weekly totals (sum of the two days’ scores computed in previous test)
    # Neon Fox: 1275 + 1210 = 2485
    # Velvet Echo: 1130 + 1365 = 2495 (slightly higher → rank 1)
    assert weekly[0]["name"] == "Velvet Echo"
    assert pytest.approx(weekly[0]["score"], rel=1e-6) == 2495.0

    assert weekly[1]["name"] == "Neon Fox"
    assert pytest.approx(weekly[1]["score"], rel=1e-6) == 2485.0
