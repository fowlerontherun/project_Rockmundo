-- 178_songwriting_completion_metadata.sql
-- Persist the writing-stage result alongside the canonical songs table.

CREATE TABLE IF NOT EXISTS songwriting_song_metadata (
  song_id INTEGER PRIMARY KEY,
  draft_id INTEGER NOT NULL UNIQUE,
  creator_id INTEGER NOT NULL,
  lyrics TEXT NOT NULL DEFAULT '',
  chord_progression TEXT NOT NULL DEFAULT '',
  themes_json TEXT NOT NULL DEFAULT '[]',
  quality_score INTEGER NOT NULL DEFAULT 1,
  writing_minutes INTEGER NOT NULL DEFAULT 0,
  initial_minutes INTEGER NOT NULL DEFAULT 0,
  revision_sessions INTEGER NOT NULL DEFAULT 0,
  revision_minutes INTEGER NOT NULL DEFAULT 0,
  polish_minutes INTEGER NOT NULL DEFAULT 0,
  polish_attempted INTEGER NOT NULL DEFAULT 0,
  polish_skipped INTEGER NOT NULL DEFAULT 0,
  polish_succeeded INTEGER,
  polish_success_chance INTEGER,
  polish_bonus INTEGER NOT NULL DEFAULT 0,
  distribution_channels_json TEXT NOT NULL DEFAULT '[]',
  songwriting_completed_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
);
-- SPLIT --
CREATE INDEX IF NOT EXISTS ix_songwriting_song_metadata_draft
ON songwriting_song_metadata(draft_id);
