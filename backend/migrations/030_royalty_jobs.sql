-- File: backend/migrations/030_royalty_jobs.sql
-- Creates tables for royalty runs and run lines (idempotent)

CREATE TABLE IF NOT EXISTS royalty_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  period_start TEXT NOT NULL,
  period_end TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending', -- pending|running|completed|failed
  notes TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS royalty_run_lines (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  work_type TEXT NOT NULL,               -- 'song' | 'album' | 'misc'
  work_id INTEGER,                        -- nullable for misc
  band_id INTEGER,                        -- owner band (if known)
  collaborator_band_id INTEGER,           -- collaborator (if split applied), else NULL
  source TEXT NOT NULL,                   -- 'streams' | 'digital' | 'vinyl'
  amount_cents INTEGER NOT NULL,          -- signed cents (>=0 usually)
  meta_json TEXT,                         -- details (e.g., counts, rates, notes)
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (run_id) REFERENCES royalty_runs(id)
);

CREATE INDEX IF NOT EXISTS ix_royalty_lines_run ON royalty_run_lines(run_id);
CREATE INDEX IF NOT EXISTS ix_royalty_lines_band ON royalty_run_lines(band_id);
CREATE INDEX IF NOT EXISTS ix_royalty_lines_work ON royalty_run_lines(work_type, work_id);
