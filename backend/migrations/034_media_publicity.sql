-- File: backend/migrations/034_media_publicity.sql
-- Idempotent schema for media/publicity

CREATE TABLE IF NOT EXISTS media_outlets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  region TEXT,
  reach_score INTEGER NOT NULL,
  url TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_media_outlets_name ON media_outlets(name);
CREATE INDEX IF NOT EXISTS ix_media_outlets_region ON media_outlets(region);
CREATE INDEX IF NOT EXISTS ix_media_outlets_type ON media_outlets(type);

CREATE TABLE IF NOT EXISTS media_campaigns (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  band_id INTEGER NOT NULL,
  outlet_id INTEGER NOT NULL,
  kind TEXT NOT NULL,
  title TEXT,
  notes TEXT,
  cost_cents INTEGER NOT NULL DEFAULT 0,
  currency TEXT DEFAULT 'USD',
  fame_boost INTEGER NOT NULL DEFAULT 0,
  start_date TEXT NOT NULL,
  end_date TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT,
  FOREIGN KEY(outlet_id) REFERENCES media_outlets(id)
);

CREATE INDEX IF NOT EXISTS ix_media_campaigns_band ON media_campaigns(band_id);
CREATE INDEX IF NOT EXISTS ix_media_campaigns_outlet ON media_campaigns(outlet_id);
CREATE INDEX IF NOT EXISTS ix_media_campaigns_status ON media_campaigns(status);
CREATE INDEX IF NOT EXISTS ix_media_campaigns_dates ON media_campaigns(start_date, end_date);

CREATE TABLE IF NOT EXISTS media_content (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  creator_id INTEGER NOT NULL,
  outlet_id INTEGER,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  media_url TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS ix_media_content_creator ON media_content(creator_id);
CREATE INDEX IF NOT EXISTS ix_media_content_outlet ON media_content(outlet_id);
CREATE INDEX IF NOT EXISTS ix_media_content_type ON media_content(type);

CREATE TABLE IF NOT EXISTS media_effects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  campaign_id INTEGER NOT NULL,
  band_id INTEGER NOT NULL,
  outlet_id INTEGER NOT NULL,
  region TEXT,
  effect_type TEXT NOT NULL,
  value_int INTEGER NOT NULL,
  notes TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(campaign_id) REFERENCES media_campaigns(id),
  FOREIGN KEY(outlet_id) REFERENCES media_outlets(id)
);

CREATE INDEX IF NOT EXISTS ix_media_effects_band ON media_effects(band_id);
CREATE INDEX IF NOT EXISTS ix_media_effects_campaign ON media_effects(campaign_id);
