-- File: backend/migrations/060_music_events.sql
BEGIN;

CREATE TABLE IF NOT EXISTS music_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_type TEXT NOT NULL,
  item_id INTEGER,
  quantity INTEGER DEFAULT 1,
  revenue REAL DEFAULT 0.0,
  meta JSON,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS ix_music_events_type_time ON music_events(event_type, created_at);
CREATE INDEX IF NOT EXISTS ix_music_events_item_time ON music_events(item_id, created_at);

COMMIT;
