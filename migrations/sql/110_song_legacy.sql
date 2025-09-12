-- 110_song_legacy.sql
-- Adds legacy tracking fields to songs.
BEGIN TRANSACTION;
ALTER TABLE songs ADD COLUMN legacy_state TEXT NOT NULL DEFAULT 'new';
ALTER TABLE songs ADD COLUMN original_release_date TEXT;
COMMIT;
