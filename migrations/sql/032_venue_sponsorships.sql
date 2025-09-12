-- File: backend/migrations/032_venue_sponsorships.sql
-- Adds tables for venue sponsorships and ad tracking.

CREATE TABLE IF NOT EXISTS venue_sponsorships (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  venue_id INTEGER NOT NULL,
  sponsor_name TEXT NOT NULL,
  sponsor_website TEXT,
  sponsor_logo_url TEXT,
  naming_pattern TEXT DEFAULT "{sponsor} {venue}", -- how name is displayed
  start_date TEXT,
  end_date TEXT,
  is_active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT,
  UNIQUE(venue_id)
);

CREATE TABLE IF NOT EXISTS sponsor_ad_impressions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sponsorship_id INTEGER NOT NULL,
  impression_time TEXT DEFAULT (datetime('now')),
  user_id INTEGER,
  placement TEXT, -- e.g., 'venue_header', 'event_page_banner'
  event_id INTEGER, -- optional: if shown on specific event
  meta_json TEXT,
  FOREIGN KEY(sponsorship_id) REFERENCES venue_sponsorships(id)
);

CREATE INDEX IF NOT EXISTS ix_sponsor_impr_sponsorship ON sponsor_ad_impressions(sponsorship_id);
CREATE INDEX IF NOT EXISTS ix_sponsor_impr_event ON sponsor_ad_impressions(event_id);
