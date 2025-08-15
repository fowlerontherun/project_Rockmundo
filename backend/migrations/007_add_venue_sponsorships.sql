-- File: backend/migrations/007_add_venue_sponsorships.sql
-- Sponsors catalogue
CREATE TABLE IF NOT EXISTS sponsors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  website_url TEXT,
  logo_url TEXT,
  contact_email TEXT,
  notes TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT
);

-- Venue sponsorships (time-bound)
CREATE TABLE IF NOT EXISTS venue_sponsorships (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  venue_id INTEGER NOT NULL,
  sponsor_id INTEGER NOT NULL,
  start_date TEXT NOT NULL,
  end_date TEXT,
  is_active INTEGER DEFAULT 1,
  naming_format TEXT DEFAULT '{sponsor} {venue}',
  show_logo INTEGER DEFAULT 1,
  show_website INTEGER DEFAULT 1,
  revenue_model TEXT DEFAULT 'CPM',
  revenue_cents_per_unit INTEGER,
  fixed_fee_cents INTEGER,
  currency TEXT DEFAULT 'USD',
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT,
  FOREIGN KEY (venue_id) REFERENCES venues(id),
  FOREIGN KEY (sponsor_id) REFERENCES sponsors(id)
);

-- Ad metrics
CREATE TABLE IF NOT EXISTS sponsorship_ad_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sponsorship_id INTEGER NOT NULL,
  event_type TEXT NOT NULL,            -- 'impression' | 'click'
  occurred_at TEXT DEFAULT (datetime('now')),
  meta_json TEXT,
  FOREIGN KEY (sponsorship_id) REFERENCES venue_sponsorships(id)
);

-- Current effective sponsorship per venue
CREATE VIEW IF NOT EXISTS v_current_venue_sponsorship AS
SELECT
  vs.*
FROM venue_sponsorships vs
WHERE
  vs.is_active = 1
  AND date(vs.start_date) <= date('now')
  AND (vs.end_date IS NULL OR date(vs.end_date) >= date('now'));
