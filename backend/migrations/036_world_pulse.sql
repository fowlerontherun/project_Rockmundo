-- File: backend/migrations/036_world_pulse.sql
-- World Pulse / Trending Genres schema (idempotent)

CREATE TABLE IF NOT EXISTS genre_pulse_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  period TEXT NOT NULL,              -- 'daily' (extensible)
  date TEXT NOT NULL,                -- YYYY-MM-DD
  region TEXT NOT NULL,              -- 'Global' or specific (e.g., 'UK')
  genre TEXT NOT NULL,
  score REAL NOT NULL,
  sources_json TEXT,                 -- JSON with component scores
  created_at TEXT DEFAULT (datetime('now')),
  UNIQUE(period, date, region, genre)
);

CREATE INDEX IF NOT EXISTS ix_pulse_date_region ON genre_pulse_snapshots(date, region);
CREATE INDEX IF NOT EXISTS ix_pulse_genre ON genre_pulse_snapshots(genre);
