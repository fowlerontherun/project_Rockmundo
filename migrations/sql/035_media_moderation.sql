-- File: backend/migrations/035_media_moderation.sql
-- Adds moderation status columns and a moderation log table for media system.

ALTER TABLE media_outlets ADD COLUMN mod_status TEXT DEFAULT 'approved';
ALTER TABLE media_outlets ADD COLUMN mod_notes TEXT;

ALTER TABLE media_campaigns ADD COLUMN mod_status TEXT DEFAULT 'pending';
ALTER TABLE media_campaigns ADD COLUMN mod_notes TEXT;

ALTER TABLE media_content ADD COLUMN mod_status TEXT DEFAULT 'pending';
ALTER TABLE media_content ADD COLUMN mod_notes TEXT;

CREATE TABLE IF NOT EXISTS media_moderation_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  object_type TEXT NOT NULL,
  object_id INTEGER NOT NULL,
  action TEXT NOT NULL,
  moderator_id INTEGER NOT NULL,
  reason TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_media_mlog_obj ON media_moderation_logs(object_type, object_id);
