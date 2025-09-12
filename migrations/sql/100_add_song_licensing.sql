-- 100_add_song_licensing.sql
-- Adds licensing fields to songs and creates cover_royalties table.
-- Safe for SQLite.

ALTER TABLE songs ADD COLUMN license_fee INTEGER DEFAULT 0;
-- SPLIT --
ALTER TABLE songs ADD COLUMN royalty_rate REAL DEFAULT 0.0;

-- SPLIT --

CREATE TABLE IF NOT EXISTS cover_royalties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id INTEGER NOT NULL,
    cover_band_id INTEGER NOT NULL,
    amount_owed INTEGER NOT NULL,
    amount_paid INTEGER DEFAULT 0,
    license_proof_url TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(song_id) REFERENCES songs(id)
);
-- SPLIT --
CREATE INDEX IF NOT EXISTS ix_cover_royalties_song ON cover_royalties(song_id);
