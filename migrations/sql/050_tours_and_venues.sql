-- File: backend/migrations/050_tours_and_venues.sql
-- Tours, Venues, and Tour Stops schema (SQLite compatible, idempotent)

-- Venues
CREATE TABLE IF NOT EXISTS venues (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  city TEXT,
  country TEXT,
  capacity INTEGER,
  created_at TEXT DEFAULT (datetime('now'))
);
-- SPLIT --
CREATE INDEX IF NOT EXISTS ix_venues_city ON venues(city);
-- SPLIT --
CREATE INDEX IF NOT EXISTS ix_venues_name ON venues(name);

-- Tours
-- SPLIT --
CREATE TABLE IF NOT EXISTS tours (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  band_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft', -- draft|confirmed|cancelled
  created_at TEXT DEFAULT (datetime('now'))
);
-- SPLIT --
CREATE INDEX IF NOT EXISTS ix_tours_band ON tours(band_id, status);

-- Tour Stops
-- SPLIT --
CREATE TABLE IF NOT EXISTS tour_stops (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tour_id INTEGER NOT NULL,
  venue_id INTEGER NOT NULL,
  date_start TEXT NOT NULL,  -- ISO date or datetime string
  date_end TEXT NOT NULL,
  order_index INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending', -- pending|confirmed|cancelled
  notes TEXT,
  is_recorded INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (tour_id) REFERENCES tours(id) ON DELETE CASCADE,
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE RESTRICT
);
-- SPLIT --
CREATE INDEX IF NOT EXISTS ix_stops_tour ON tour_stops(tour_id, order_index);
-- SPLIT --
CREATE INDEX IF NOT EXISTS ix_stops_venue_dates ON tour_stops(venue_id, date_start, date_end);
