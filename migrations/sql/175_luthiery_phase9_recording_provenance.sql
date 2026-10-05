CREATE TABLE IF NOT EXISTS luthiery_recording_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, band_id INTEGER NOT NULL, track_id INTEGER NOT NULL,
 session_key TEXT NOT NULL, recorded_at TEXT NOT NULL DEFAULT(datetime('now')),
 UNIQUE(band_id,track_id,session_key)
);
