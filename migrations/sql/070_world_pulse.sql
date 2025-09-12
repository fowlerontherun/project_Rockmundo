-- 070_world_pulse.sql
-- World Pulse metrics, rankings, and weekly cache


-- Optional: minimal job metadata table if your project doesn't already have one.
CREATE TABLE IF NOT EXISTS job_metadata (
  job_name   TEXT NOT NULL,
  run_at     TEXT NOT NULL,   -- ISO timestamp
  status     TEXT NOT NULL,   -- 'ok' | 'error'
  details    TEXT,            -- JSON or text
  PRIMARY KEY (job_name, run_at)
);

-- Optional: minimal app_config KV table for weights or future knobs
-- SPLIT --
CREATE TABLE IF NOT EXISTS app_config (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- Daily per-artist metrics
-- SPLIT --
CREATE TABLE IF NOT EXISTS world_pulse_metrics (
  date           TEXT NOT NULL,  -- YYYY-MM-DD (UTC or project-local convention)
  artist_id      INTEGER NOT NULL,
  streams        INTEGER NOT NULL DEFAULT 0,
  sales_digital  INTEGER NOT NULL DEFAULT 0,
  sales_vinyl    INTEGER NOT NULL DEFAULT 0,
  score          REAL    NOT NULL DEFAULT 0,
  season         TEXT,
  PRIMARY KEY (date, artist_id)
);
-- SPLIT --
CREATE INDEX IF NOT EXISTS idx_world_pulse_metrics_date ON world_pulse_metrics(date);
-- SPLIT --
CREATE INDEX IF NOT EXISTS idx_world_pulse_metrics_artist ON world_pulse_metrics(artist_id);

-- Daily rankings (toplist for a given date)
-- SPLIT --
CREATE TABLE IF NOT EXISTS world_pulse_rankings (
  date        TEXT    NOT NULL,
  season      TEXT,
  rank        INTEGER NOT NULL,
  artist_id   INTEGER NOT NULL,
  name        TEXT    NOT NULL,
  pct_change  REAL,             -- vs previous day (fraction, e.g. 0.12 = +12%)
  score       REAL    NOT NULL,
  PRIMARY KEY (date, season, rank)
);
-- SPLIT --
CREATE INDEX IF NOT EXISTS idx_world_pulse_rankings_artist ON world_pulse_rankings(artist_id);

-- Weekly cache (rollup of daily → weekly)
-- SPLIT --
CREATE TABLE IF NOT EXISTS world_pulse_weekly_cache (
  week_start  TEXT    NOT NULL, -- Monday (YYYY-MM-DD)
  rank        INTEGER NOT NULL,
  artist_id   INTEGER NOT NULL,
  name        TEXT    NOT NULL,
  pct_change  REAL,             -- vs previous week (fraction)
  score       REAL    NOT NULL, -- weekly total score (sum of daily)
  PRIMARY KEY (week_start, rank)
);
-- SPLIT --
CREATE INDEX IF NOT EXISTS idx_world_pulse_weekly_artist ON world_pulse_weekly_cache(artist_id);
