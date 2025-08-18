-- File: backend/migrations/031_charts.sql
-- Snapshot tables for charts (daily/weekly) per channel and combined.

CREATE TABLE IF NOT EXISTS chart_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  chart_type TEXT NOT NULL,        -- e.g., 'streams_song','digital_song','digital_album','vinyl_album','combined_song','combined_album'
  period TEXT NOT NULL,            -- 'daily' | 'weekly'
  period_start TEXT NOT NULL,
  period_end TEXT NOT NULL,
  rank INTEGER NOT NULL,
  work_type TEXT NOT NULL,         -- 'song' | 'album'
  work_id INTEGER NOT NULL,
  band_id INTEGER,
  title TEXT,
  metric_value REAL NOT NULL,      -- channel-specific count or normalized score
  source_notes TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  UNIQUE(chart_type, period, period_start, rank)
);

CREATE INDEX IF NOT EXISTS ix_charts_period ON chart_snapshots(period, period_start);
CREATE INDEX IF NOT EXISTS ix_charts_work ON chart_snapshots(work_type, work_id);
