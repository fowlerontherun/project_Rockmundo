-- File: backend/migrations/060_music_sales_streams.sql
-- Sales (digital + vinyl) and Streams with a unified metrics view (SQLite-compatible, idempotent)


-- Albums
CREATE TABLE IF NOT EXISTS albums (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  band_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  release_date TEXT,
  type TEXT DEFAULT 'album',
  created_at TEXT DEFAULT (datetime('now'))
);
-- SPLIT --
CREATE INDEX IF NOT EXISTS ix_albums_band ON albums(band_id);

-- Songs
-- SPLIT --
CREATE TABLE IF NOT EXISTS songs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  album_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  track_no INTEGER,
  length_sec INTEGER,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
);
-- SPLIT --
CREATE INDEX IF NOT EXISTS ix_songs_album ON songs(album_id);

-- Digital sales
-- SPLIT --
CREATE TABLE IF NOT EXISTS sales_digital (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  song_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL DEFAULT 1,
  unit_price_cents INTEGER NOT NULL DEFAULT 0,
  currency TEXT DEFAULT 'USD',
  sold_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
);
-- SPLIT --
CREATE INDEX IF NOT EXISTS ix_sales_digital_song ON sales_digital(song_id, sold_at);

-- Vinyl sales
-- SPLIT --
CREATE TABLE IF NOT EXISTS sales_vinyl (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  album_id INTEGER NOT NULL,
  variant TEXT DEFAULT 'standard',
  quantity INTEGER NOT NULL DEFAULT 1,
  unit_price_cents INTEGER NOT NULL DEFAULT 0,
  currency TEXT DEFAULT 'USD',
  sold_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
);
-- SPLIT --
CREATE INDEX IF NOT EXISTS ix_sales_vinyl_album ON sales_vinyl(album_id, sold_at);

-- Streams
-- SPLIT --
CREATE TABLE IF NOT EXISTS streams (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  song_id INTEGER NOT NULL,
  platform TEXT NOT NULL,
  country TEXT DEFAULT 'US',
  count INTEGER NOT NULL DEFAULT 1,
  streamed_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
);
-- SPLIT --
CREATE INDEX IF NOT EXISTS ix_streams_song ON streams(song_id, streamed_at);
-- SPLIT --
CREATE INDEX IF NOT EXISTS ix_streams_platform ON streams(platform);

-- Unified view
-- SPLIT --
DROP VIEW IF EXISTS music_ledger_view;
-- SPLIT --
CREATE VIEW music_ledger_view AS
  SELECT 'digital_sale' AS event_type, sd.sold_at AS occurred_at, s.id AS song_id, s.album_id AS album_id,
         sd.quantity AS units, (sd.quantity * sd.unit_price_cents) AS revenue_cents, sd.currency AS currency, NULL AS platform
  FROM sales_digital sd JOIN songs s ON s.id = sd.song_id
UNION ALL
  SELECT 'vinyl_sale' AS event_type, sv.sold_at AS occurred_at, NULL AS song_id, sv.album_id AS album_id,
         sv.quantity AS units, (sv.quantity * sv.unit_price_cents) AS revenue_cents, sv.currency AS currency, NULL AS platform
  FROM sales_vinyl sv
UNION ALL
  SELECT 'stream' AS event_type, st.streamed_at AS occurred_at, st.song_id AS song_id, s.album_id AS album_id,
         st.count AS units, 0 AS revenue_cents, 'USD' AS currency, st.platform AS platform
  FROM streams st JOIN songs s ON s.id = st.song_id;
