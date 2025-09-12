-- 095_add_original_song_id.sql
-- Adds original_song_id column to songs for tracking covers.
-- Safe for SQLite.
BEGIN TRANSACTION;

ALTER TABLE songs ADD COLUMN original_song_id INTEGER REFERENCES songs(id);
CREATE INDEX IF NOT EXISTS ix_songs_original_song ON songs(original_song_id);

COMMIT;
