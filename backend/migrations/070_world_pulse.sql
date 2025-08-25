-- File: backend/migrations/070_world_pulse.sql
-- World Pulse metrics + rankings (SQLite, idempotent)

BEGIN;

-- Metrics per band per day (aggregated from music_ledger_view)
CREATE TABLE IF NOT EXISTS world_pulse_metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pulse_date TEXT NOT NULL,            -- YYYY-MM-DD
  band_id INTEGER NOT NULL,
  streams INTEGER NOT NULL DEFAULT 0,
  digital_units INTEGER NOT NULL DEFAULT 0,
  vinyl_units INTEGER NOT NULL DEFAULT 0,
  score INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  UNIQUE (pulse_date, band_id)
);
CREATE INDEX IF NOT EXISTS ix_pulse_day ON world_pulse_metrics(pulse_date, score);

-- Rankings snapshot (daily or weekly period)
CREATE TABLE IF NOT EXISTS world_pulse_rankings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  period TEXT NOT NULL,                -- 'daily' | 'weekly'
  pulse_date TEXT NOT NULL,            -- anchor day (YYYY-MM-DD)
  band_id INTEGER NOT NULL,
  rank INTEGER NOT NULL,
  score INTEGER NOT NULL,
  pct_change REAL,                     -- vs previous period
  trend TEXT,                          -- 'up' | 'down' | 'flat'
  created_at TEXT DEFAULT (datetime('now')),
  UNIQUE (period, pulse_date, band_id)
);
CREATE INDEX IF NOT EXISTS ix_pulse_rank ON world_pulse_rankings(period, pulse_date, rank);

-- Optional compact cache for the weekly widget
CREATE TABLE IF NOT EXISTS world_pulse_weekly_cache (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pulse_week TEXT NOT NULL,            -- YYYY-WW (ISO week-ish), or anchor YYYY-MM-DD of week start
  payload_json TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now')),
  UNIQUE (pulse_week)
);

COMMIT;
