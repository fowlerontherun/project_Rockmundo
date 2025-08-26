-- 075_job_history.sql
-- Tracks each job run with status, duration, and rows affected.

BEGIN;

CREATE TABLE IF NOT EXISTS job_history (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  job_name         TEXT NOT NULL,
  started_at       TEXT NOT NULL,         -- ISO8601 UTC
  finished_at      TEXT,                  -- ISO8601 UTC
  status           TEXT NOT NULL,         -- 'success' | 'error' | 'running'
  duration_ms      INTEGER,               -- computed on finish
  rows_affected    INTEGER DEFAULT 0,     -- for cleanup jobs
  detail           TEXT,                  -- free-form details
  error            TEXT                   -- error message (if any)
);

CREATE INDEX IF NOT EXISTS idx_job_history_name_started
  ON job_history (job_name, started_at DESC);

COMMIT;
