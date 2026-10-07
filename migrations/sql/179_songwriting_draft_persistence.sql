-- 179_songwriting_draft_persistence.sql
-- Durable songwriting drafts, collaborators, invitations and version history.

CREATE TABLE IF NOT EXISTS songwriting_drafts (
  id INTEGER PRIMARY KEY,
  creator_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  genre TEXT NOT NULL,
  themes_json TEXT NOT NULL DEFAULT '[]',
  lyrics TEXT NOT NULL DEFAULT '',
  chord_progression TEXT NOT NULL DEFAULT '',
  album_art_url TEXT,
  plagiarism_warning TEXT,
  created_at TEXT NOT NULL,
  quality_modifier REAL NOT NULL DEFAULT 1.0,
  chemistry REAL,
  status TEXT NOT NULL DEFAULT 'draft',
  completed_at TEXT,
  writing_minutes INTEGER NOT NULL DEFAULT 60,
  revision_sessions INTEGER NOT NULL DEFAULT 0,
  quality_score INTEGER,
  polish_available INTEGER NOT NULL DEFAULT 0,
  polish_attempted INTEGER NOT NULL DEFAULT 0,
  polish_success_chance INTEGER,
  polish_succeeded INTEGER,
  polish_skipped INTEGER NOT NULL DEFAULT 0,
  polish_bonus INTEGER NOT NULL DEFAULT 0
);
-- SPLIT --
CREATE TABLE IF NOT EXISTS songwriting_co_writers (
  draft_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  PRIMARY KEY (draft_id, user_id),
  FOREIGN KEY (draft_id) REFERENCES songwriting_drafts(id) ON DELETE CASCADE
);
-- SPLIT --
CREATE TABLE IF NOT EXISTS songwriting_co_writer_invites (
  draft_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  inviter_id INTEGER NOT NULL,
  PRIMARY KEY (draft_id, user_id),
  FOREIGN KEY (draft_id) REFERENCES songwriting_drafts(id) ON DELETE CASCADE
);
-- SPLIT --
CREATE TABLE IF NOT EXISTS songwriting_draft_versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  draft_id INTEGER NOT NULL,
  author_id INTEGER NOT NULL,
  lyrics TEXT NOT NULL,
  chord_progression TEXT,
  themes_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  FOREIGN KEY (draft_id) REFERENCES songwriting_drafts(id) ON DELETE CASCADE
);
-- SPLIT --
CREATE INDEX IF NOT EXISTS ix_songwriting_drafts_creator
ON songwriting_drafts(creator_id, created_at);
-- SPLIT --
CREATE INDEX IF NOT EXISTS ix_songwriting_invites_user
ON songwriting_co_writer_invites(user_id, draft_id);
